import torch
from hydra import compose, initialize
from hydra.utils import instantiate
from omegaconf import OmegaConf
import os

HF_MODEL_ID_TO_FILENAMES = {
    "apple/fastvit-t8": (
        "fastvit_t8.yaml",
        "fastvit_t8_reparam.pth.tar",
    ),
    "apple/fastvit-t12": (
        "fastvit_t12.yaml",
        "fastvit_t12_reparam.pth.tar",
    ),
    "apple/fastvit-s12": (
        "fastvit_s12.yaml",
        "fastvit_s12_reparam.pth.tar",
    ),
    "apple/fastvit-sa12": (
        "fastvit_sa12.yaml",
        "fastvit_sa12_reparam.pth.tar",
    ),
    "apple/fastvit-sa24": (
        "fastvit_sa24.yaml",
        "fastvit_sa24_reparam.pth.tar",
    ),
    "apple/fastvit-sa36": (
        "fastvit_sa36.yaml",
        "fastvit_sa36_reparam.pth.tar",
    ),
    "apple/fastvit-ma36": (
        "fastvit_ma36.yaml",
        "fastvit_ma36_reparam.pth.tar",
    ),
}

def build_fastvit(
    config_file,
    ckpt_path=None,
    device="cuda",
    mode="eval",
    hydra_overrides_extra=[],
    **kwargs,
):
    config_path = "fastvit/configs"
    config_name = config_file
    if config_name.endswith(".yaml"):
        config_name = config_name[:-5]
    from hydra.core.global_hydra import GlobalHydra
    if GlobalHydra.instance().is_initialized():
        GlobalHydra.instance().clear()
    with initialize(config_path=config_path, job_name="fastvit_job"):
        cfg = compose(config_name=config_name, overrides=hydra_overrides_extra)
        OmegaConf.resolve(cfg)
        model = instantiate(cfg.model, _recursive_=True)
        if ckpt_path is not None:
            sd = torch.load(ckpt_path, map_location="cpu", weights_only=False)
            if "state_dict" in sd:
                sd = sd["state_dict"]
            elif "model" in sd:
                sd = sd["model"]
            model.load_state_dict(sd, strict=False)
        model = model.to(device)
        if mode == "eval":
            model.eval()
        return model

def _hf_download(model_id):
    from huggingface_hub import hf_hub_download
    config_name, checkpoint_name = HF_MODEL_ID_TO_FILENAMES[model_id]
    ckpt_path = hf_hub_download(repo_id=model_id, filename=checkpoint_name)
    return config_name, ckpt_path

def build_fastvit_hf(model_id, **kwargs):
    config_name, ckpt_path = _hf_download(model_id)
    return build_fastvit(config_file=config_name, ckpt_path=ckpt_path, **kwargs)