# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.

import os
import sys
import logging
import torch
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from tsm.model.segmentation_model.builder import build_sam2
from tsm.model.segmentation_model.sam2.sam2_image_predictor import SAM2ImagePredictor

def main():
	logging.basicConfig(level=logging.INFO)
	# Example config and checkpoint paths (edit as needed)
	config_file = "sam2.1/sam2.1_hiera_s.yaml"
	ckpt_path = "/mnt/data/coden/Multi-Organ-Tumor-Segmentation-Application/tsm/checkpoints/sam2/sam2.1_hiera_small.pt"
	device = "cuda" if torch.cuda.is_available() else "cpu"

	# Load model
	model = build_sam2(config_file=config_file, ckpt_path=ckpt_path, device=device)
	predictor = SAM2ImagePredictor(model)

	# Load test image (edit path as needed)
	img_path = "/mnt/data/coden/Multi-Organ-Tumor-Segmentation-Application/resource/images/Nokota_Horses_cropped.jpg"
	if not os.path.exists(img_path):
		logging.error(f"Test image not found: {img_path}")
		return
	image = Image.open(img_path).convert("RGB")

	# Set image for predictor
	predictor.set_image(image)

	# Example: single point prompt at image center
	w, h = image.size
	point_coords = np.array([[w // 2, h // 2]])
	point_labels = np.array([1])  # 1: foreground

	# Predict mask
	masks, ious, low_res_masks = predictor.predict(
		point_coords=point_coords,
		point_labels=point_labels,
		multimask_output=True
	)

	logging.info(f"Predicted mask shape: {masks.shape}")
	logging.info(f"Predicted IOUs: {ious}")
	# Save mask for visual check
	mask_img = Image.fromarray((masks[0] * 255).astype(np.uint8))
	mask_img.save("test/assets/pred_mask.png")
	logging.info("Saved predicted mask to test/assets/pred_mask.png")

if __name__ == "__main__":
	main()
