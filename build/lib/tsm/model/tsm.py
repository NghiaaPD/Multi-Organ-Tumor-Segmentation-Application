import torch
import torch.nn as nn

from collections import OrderedDict

from tsm.model.classification_model import builder as cls_builder
from tsm.model.classification_model.fastvit.fastvit_predictor import FastViTPredictor
from tsm.model.segmentation_model import builder as seg_builder
from tsm.model.segmentation_model.sam2.sam2_image_predictor import SAM2ImagePredictor

from tsm.model.utils import _to_numpy_image

class TwoStageModel(nn.Module):
    """
    Improved Two-Stage Model with:
    - Robust input handling for SAM2
    - Memory-efficient segmentation predictor cache (LRU)
    - Better inference performance (inference_mode + autocast)
    """
    def __init__(
        self,
        class_model_cfg,
        class_to_seg_ckpt_cfg,
        device="cuda",
        max_seg_cache_size=3,  # Giới hạn số SAM2 model giữ trong GPU cùng lúc
    ):
        super().__init__()
        self.class_model_cfg = class_model_cfg
        self.class_to_seg_ckpt_cfg = class_to_seg_ckpt_cfg
        self.device = device
        self.max_seg_cache_size = max_seg_cache_size

        self.classification_predictor = None
        # OrderedDict để dễ implement LRU: move_to_end khi access
        self.segmentation_predictors = OrderedDict()

    def get_classification_predictor(self):
        if self.classification_predictor is None:
            model = cls_builder.build_fastvit(
                config_file=self.class_model_cfg['config_file'],
                ckpt_path=self.class_model_cfg.get('ckpt_path', None),
                device=self.device,
                mode="eval",
            )
            model.eval()
            self.classification_predictor = FastViTPredictor(model, device=self.device)
        return self.classification_predictor

    def _manage_cache(self, class_idx):
        """LRU cache management: move accessed item to end, evict oldest if full"""
        if class_idx in self.segmentation_predictors:
            self.segmentation_predictors.move_to_end(class_idx)
        while len(self.segmentation_predictors) > self.max_seg_cache_size:
            oldest_class, oldest_predictor = self.segmentation_predictors.popitem(last=False)
            print(f"[Cache] Unloading segmentation model for class {oldest_class} to save GPU memory")

    def get_segmentation_predictor(self, class_idx):
        if class_idx not in self.segmentation_predictors:
            if class_idx not in self.class_to_seg_ckpt_cfg:
                raise ValueError(f"No segmentation config/ckpt for class {class_idx}")

            config_file, ckpt_path = self.class_to_seg_ckpt_cfg[class_idx]
            seg_model = seg_builder.build_sam2(
                config_file=config_file,
                ckpt_path=ckpt_path,
                device=self.device,
            )
            seg_model.eval()
            predictor = SAM2ImagePredictor(seg_model)

            # Quản lý cache trước khi thêm mới
            self._manage_cache(class_idx)
            self.segmentation_predictors[class_idx] = predictor

        else:
            # Move to end (most recently used)
            self.segmentation_predictors.move_to_end(class_idx)

        return self.segmentation_predictors[class_idx]

    @torch.inference_mode()
    def forward(self, x, *args, **kwargs):
        """
        x: input image (torch.Tensor, np.ndarray, hoặc PIL.Image)
        *args, **kwargs: prompt cho SAM2 (point_coords, box, mask_input, multimask_output, ...)
        """
        # ==================== Stage 1: Classification ====================
        cls_predictor = self.get_classification_predictor()

        cls_predictor.set_image(x)
        class_pred = cls_predictor.predict()

        if isinstance(class_pred, torch.Tensor):
            if class_pred.ndim > 1:
                class_idx = int(class_pred.argmax(dim=1).cpu().item())
            else:
                class_idx = int(class_pred.cpu().item())
        else:
            class_idx = int(class_pred)

        # ==================== Stage 2: Segmentation ====================
        seg_predictor = self.get_segmentation_predictor(class_idx)

        img_for_seg = _to_numpy_image(x)
        seg_predictor.set_image(img_for_seg)

        with torch.autocast(device_type="cuda", dtype=torch.bfloat16, enabled=(self.device == "cuda")):
            masks, ious, low_res_masks = seg_predictor.predict(*args, **kwargs)

        return masks, ious, low_res_masks
