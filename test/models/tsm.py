import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import os
import torch
import numpy as np
from PIL import Image
import torchvision.transforms as T
from loguru import logger
from tsm.model.builder import build_two_stage_model

def main():
	logger.info("=== TwoStageModel Test Pipeline Start ===")
	# Config cho classification và segmentation
	class_model_cfg = {
		'config_file': 'fastvit_ma36.yaml',
		'ckpt_path': 'tsm/checkpoints/fastvit/fastvit_ma36.pth.tar',
	}
	class_to_seg_ckpt_cfg = {
		339: ("sam2.1/sam2.1_hiera_s.yaml", "/mnt/data/coden/Multi-Organ-Tumor-Segmentation-Application/tsm/checkpoints/sam2/sam2.1_hiera_small.pt"),
		1: ("sam2.1/sam2.1_hiera_b+.yaml", "/mnt/data/coden/Multi-Organ-Tumor-Segmentation-Application/tsm/checkpoints/sam2/sam2.1_hiera_base_plus.pt"),
		# Thêm các class khác nếu cần
	}
	device = "cuda" if torch.cuda.is_available() else "cpu"

	# Build TwoStageModel
	logger.info("Building TwoStageModel...")
	model = build_two_stage_model(
		class_model_cfg=class_model_cfg,
		class_to_seg_ckpt_cfg=class_to_seg_ckpt_cfg,
		device=device,
		max_seg_cache_size=2,
	)
	logger.success("TwoStageModel built!")

	# Load ảnh test
	img_path = "/mnt/data/coden/Multi-Organ-Tumor-Segmentation-Application/resource/images/Nokota_Horses_cropped.jpg"
	if not os.path.exists(img_path):
		logger.warning(f"Test image not found: {img_path}, creating dummy image.")
		img = Image.new("RGB", (256, 256), color=(123, 222, 111))
		img.save(img_path)
	else:
		img = Image.open(img_path).convert("RGB")
	logger.info(f"Loaded test image: {img_path} size={img.size}")

	# Transform cho classification (giống cls_m.py)
	transform = T.Compose([
		T.Resize((256, 256)),
		T.ToTensor(),
		T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
	])
	input_tensor = transform(img).unsqueeze(0)
	logger.info(f"Input tensor shape for classification: {input_tensor.shape}")

	# Prompt cho segmentation (giống seg_m.py)
	w, h = img.size
	point_coords = np.array([[w // 2, h // 2]])
	point_labels = np.array([1])
	logger.info(f"Prompt for segmentation: point_coords={point_coords}, point_labels={point_labels}")

	# Inference
	logger.info("Running TwoStageModel inference...")
	masks, ious, low_res_masks = model(
		input_tensor,
		point_coords=point_coords,
		point_labels=point_labels,
		multimask_output=True
	)
	logger.success(f"Predicted mask shape: {getattr(masks, 'shape', type(masks))}")
	logger.info(f"Predicted IOUs: {ious}")
	# Save mask
	mask_img = Image.fromarray((masks[0] * 255).astype(np.uint8))
	os.makedirs("test/assets", exist_ok=True)
	mask_img.save("test/assets/pred_mask_tsm.png")
	logger.success("Saved predicted mask to test/assets/pred_mask_tsm.png")

if __name__ == "__main__":
	main()
