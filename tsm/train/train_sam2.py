import os
import json
import cv2
from loguru import logger
import torch
import plotly
import numpy as np
from dataclasses import dataclass
from sklearn.model_selection import train_test_split

from utils import Dataloader, Dataprocessor

from tsm.model.segmentation_model.builder import build_sam2
from tsm.model.segmentation_model.sam2.sam2_image_predictor import SAM2ImagePredictor

from dataclasses import dataclass, field
from typing import Literal

@dataclass
class ModelArguments:
    """
    Arguments pertaining to which model/config/checkpoint we are fine-tuning.
    """
    model_name_or_path: str = field(
        default="facebook/sam2-hiera-small",
        metadata={"help": "Path to pretrained SAM2 checkpoint or model identifier from huggingface.co/models"}
    )
    config_name: str = field(
        default="sam2_hiera_s.yaml",  # hoặc t.yaml, b.yaml, l.yaml tùy checkpoint
        metadata={"help": "SAM2 config file name (inside the repo)"}
    )
    checkpoint_path: str = field(
        default=None,
        metadata={"help": "Local path to SAM2 checkpoint .pt file. If provided, overrides model_name_or_path"}
    )
    model_size: Literal["tiny", "small", "base", "large"] = field(
        default="small",
        metadata={"help": "Size of SAM2 model: tiny, small, base, large"}
    )
    freeze_image_encoder: bool = field(
        default=True,
        metadata={"help": "Freeze the image encoder (Hiera backbone). Recommended for fine-tuning."}
    )
    freeze_prompt_encoder: bool = field(
        default=False,
        metadata={"help": "Freeze prompt encoder. Usually keep trainable."}
    )
    freeze_mask_decoder: bool = field(
        default=False,
        metadata={"help": "Freeze mask decoder. Usually trainable for fine-tuning."}
    )
    multimask_output: bool = field(
        default=True,
        metadata={"help": "Whether to output multiple masks or single best mask"}
    )

@dataclass
class DataArguments:
    """
    Arguments pertaining to data loading and preprocessing.
    """
    data_path: str = field(
        default="data/train.json",
        metadata={"help": "Path to JSON file containing list of {'image': ..., 'label_mask': ...}"}
    )
    val_data_path: str = field(
        default=None,
        metadata={"help": "Path to validation JSON file. If None, will split from train."}
    )
    train_split: float = field(
        default=0.9,
        metadata={"help": "Train split ratio if val_data_path is None"}
    )
    max_image_size: int = field(
        default=1024,
        metadata={"help": "Maximum long side for image resizing (SAM2 recommended)"}
    )
    num_points_per_mask: int = field(
        default=1,
        metadata={"help": "Number of positive points to sample per object/instance"}
    )
    max_points_per_image: int = field(
        default=32,
        metadata={"help": "Maximum total points per image to prevent OOM"}
    )
    add_negative_points: bool = field(
        default=True,
        metadata={"help": "Add negative points from background"}
    )
    num_negative_points: int = field(
        default=1,
        metadata={"help": "Number of negative points per positive point (if add_negative_points=True)"}
    )
    erode_kernel_size: int = field(
        default=5,
        metadata={"help": "Kernel size for eroding mask to sample interior points"}
    )
    erode_iterations: int = field(
        default=1,
        metadata={"help": "Iterations for erosion"}
    )

@dataclass
class TrainingArguments:
    """
    Arguments pertaining to training loop.
    """
    output_dir: str = field(
        default="outputs/sam2_finetuned",
        metadata={"help": "Directory to save model checkpoints"}
    )
    num_train_steps: int = field(
        default=3000,
        metadata={"help": "Total number of training steps"}
    )
    batch_size: int = field(
        default=1,
        metadata={"help": "Batch size per GPU. Usually 1 for SAM2 due to variable prompts"}
    )
    gradient_accumulation_steps: int = field(
        default=4,
        metadata={"help": "Gradient accumulation to simulate larger batch"}
    )
    learning_rate: float = field(
        default=1e-4,
        metadata={"help": "Initial learning rate"}
    )
    weight_decay: float = field(
        default=1e-4,
        metadata={"help": "Weight decay for AdamW"}
    )
    lr_scheduler_type: str = field(
        default="step",
        metadata={"help": "Type: 'step', 'cosine', 'linear'"}
    )
    lr_step_size: int = field(
        default=500,
        metadata={"help": "Step size for StepLR"}
    )
    lr_gamma: float = field(
        default=0.2,
        metadata={"help": "Gamma for StepLR"}
    )
    warmup_steps: int = field(
        default=100,
        metadata={"help": "Number of warmup steps"}
    )
    mixed_precision: bool = field(
        default=True,
        metadata={"help": "Use AMP (Automatic Mixed Precision)"}
    )
    grad_clip_norm: float = field(
        default=1.0,
        metadata={"help": "Gradient clipping norm"}
    )
    eval_steps: int = field(
        default=500,
        metadata={"help": "Evaluate and save every N steps"}
    )
    save_steps: int = field(
        default=1000,
        metadata={"help": "Save checkpoint every N steps"}
    )
    logging_steps: int = field(
        default=50,
        metadata={"help": "Log training metrics every N steps"}
    )
    seed: int = field(
        default=42,
        metadata={"help": "Random seed for reproducibility"}
    )
    device: str = field(
        default="cuda",
        metadata={"help": "Device to train on"}
    )

class SAMDataloader(Dataloader):
    def __init__(self, data_path, transform=None, mask_transform=None):
        super().__init__(data_path, transform, mask_transform)

class SAMDataprocessor(Dataprocessor):
    def __init__(self):
        super().__init__()

    def create_prompt_from_mask(self, img, mask, num_points_per_mask=1, add_negative=False, prompt_type="point"):
        """
        Tạo prompt (ví dụ: points) cho SAM-2 từ mask.
        img: numpy array hoặc PIL Image (RGB, uint8)
        mask: numpy array (giá trị 0 là nền, >0 là object/instance labels)
        num_points_per_mask: Số points sample per object (default 1)
        add_negative: Thêm negative points (default False)
        prompt_type: "point" (có thể mở rộng cho box, ...)
        Trả về: points (np.ndarray [N, 2]), labels (np.ndarray [N]) - 1: positive, 0: negative
        """
        import cv2
        import numpy as np
        if not isinstance(img, np.ndarray):
            Img = np.array(img)
        else:
            Img = img
        if not isinstance(mask, np.ndarray):
            ann_map = np.array(mask)
        else:
            ann_map = mask

        # Resize về max 1024 nếu cần (giữ uint8 cho image)
        r = min(1024 / Img.shape[1], 1024 / Img.shape[0])
        if r < 1.0:
            Img = cv2.resize(Img, (int(Img.shape[1] * r), int(Img.shape[0] * r)))
            ann_map = cv2.resize(ann_map, (int(ann_map.shape[1] * r), int(ann_map.shape[0] * r)), interpolation=cv2.INTER_NEAREST)

        # Xử lý multi-instance: unique labels
        inds = np.unique(ann_map)[1:]  # Bỏ background (0)
        points = []
        labels = []

        for ind in inds:
            obj_mask = (ann_map == ind).astype(np.uint8)
            eroded_mask = cv2.erode(obj_mask, np.ones((5, 5), np.uint8), iterations=1)
            coords = np.argwhere(eroded_mask > 0)
            if len(coords) == 0:
                continue
            for _ in range(num_points_per_mask):
                idx = np.random.randint(len(coords))
                yx = coords[idx]
                points.append([yx[1], yx[0]])  # [x, y]
                labels.append(1)  # positive

        # Optional: Thêm negative points (từ background)
        if add_negative:
            neg_coords = np.argwhere(ann_map == 0)
            if len(neg_coords) > 0:
                num_neg = len(points)  # Cân bằng số lượng
                for _ in range(num_neg):
                    idx = np.random.randint(len(neg_coords))
                    yx = neg_coords[idx]
                    points.append([yx[1], yx[0]])
                    labels.append(0)  # negative

        points = np.array(points)
        labels = np.array(labels)
        return points, labels

def maybe_zero_3(param, ignore_status=False, name=None):
    from deepspeed import zero
    from deepspeed.runtime.zero.partition_parameters import ZeroParamStatus
    if hasattr(param, "ds_id"):
        if param.ds_status == ZeroParamStatus.NOT_AVAILABLE:
            if not ignore_status:
                logger.warning(f"{name}: param.ds_status != ZeroParamStatus.NOT_AVAILABLE: {param.ds_status}")
        with zero.GatheredParameters([param]):
            param = param.data.detach().cpu().clone()
    else:
        param = param.detach().cpu().clone()
    return param

def train():
    pass