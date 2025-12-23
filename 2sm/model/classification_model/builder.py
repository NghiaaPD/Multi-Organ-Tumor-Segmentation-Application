import os
import torch
from hydra import compose
from hydra.utils import instantiate
from omegaconf import OmegaConf

import fastvit.modeling.fastvit as fastvit

def build_fastvit(
    config_file,
    ckpt_path=None,
    device="cuda",
    mode="eval",
    hydra_overrides_extra=[],
    **kwargs,
):
    # Read config and init model
    cfg = compose(config_name=config_file, overrides=hydra_overrides_extra)
    OmegaConf.resolve(cfg)
    model = instantiate(cfg.model, _recursive_=True)
    if ckpt_path is not None:
        sd = torch.load(ckpt_path, map_location="cpu")
        if "model" in sd:
            sd = sd["model"]
        model.load_state_dict(sd)
    model = model.to(device)
    if mode == "eval":
        model.eval()
    return model