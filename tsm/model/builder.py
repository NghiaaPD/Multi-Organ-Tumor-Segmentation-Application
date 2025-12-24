
# TwoStageModel builder
def build_two_stage_model(
	class_model_cfg,
	class_to_seg_ckpt_cfg,
	device="cuda",
	max_seg_cache_size=3,
):
	"""
	Build a TwoStageModel (classification + segmentation pipeline).
	Args:
		class_model_cfg: dict, config for classification model (see tsm.py)
		class_to_seg_ckpt_cfg: dict, mapping class index to (config_file, ckpt_path)
		device: device for model
		max_seg_cache_size: max number of segmentation models cached in GPU
	Returns:
		TwoStageModel instance
	"""
	from tsm.model.tsm import TwoStageModel
	return TwoStageModel(
		class_model_cfg=class_model_cfg,
		class_to_seg_ckpt_cfg=class_to_seg_ckpt_cfg,
		device=device,
		max_seg_cache_size=max_seg_cache_size,
	)
