import torch
from timm.models import create_model

def fastvit_predict(model, input_tensor=None, device="cuda"):
    if isinstance(model, str):
        model = create_model(model)
    model = model.to(device)
    model.eval()
    from .modeling.modules.mobileone import reparameterize_model
    model_inf = reparameterize_model(model)
    model_inf = model_inf.to(device)
    with torch.no_grad():
        output = model_inf(input_tensor.to(device))
    return output