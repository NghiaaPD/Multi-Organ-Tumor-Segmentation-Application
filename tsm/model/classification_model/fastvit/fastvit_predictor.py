
import torch
from timm.models import create_model

class FastViTPredictor:
    def __init__(self, model, device="cuda"):
        """
        model: str (model name) hoặc instance đã khởi tạo
        """
        if isinstance(model, str):
            model = create_model(model)
        self.model = model.to(device)
        self.model.eval()
        from .modeling.modules.mobileone import reparameterize_model
        self.model_inf = reparameterize_model(self.model)
        self.model_inf = self.model_inf.to(device)
        self.device = device
        self._input = None
        self._output = None

    def set_image(self, input_tensor):
        """
        Lưu input để inference (giống set_image của SAM2ImagePredictor)
        """
        self._input = input_tensor

    @torch.no_grad()
    def predict(self, input_tensor=None):
        """
        Dự đoán class cho input_tensor (nếu không truyền thì dùng self._input)
        """
        if input_tensor is None:
            input_tensor = self._input
        if input_tensor is None:
            raise ValueError("No input_tensor provided for prediction.")
        output = self.model_inf(input_tensor.to(self.device))
        self._output = output
        return output