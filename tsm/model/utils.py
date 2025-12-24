import torch
import numpy as np
from PIL import Image


def _to_numpy_image(img):
    """
    Convert various input types to numpy uint8 RGB (H, W, 3) required by SAM2.
    """
    if isinstance(img, np.ndarray):
        if img.dtype != np.uint8:
            img = (img * 255).astype(np.uint8) if img.max() <= 1.0 else img.astype(np.uint8)
        if img.shape[-1] == 3:  # HWC
            img = img[..., ::-1] if img.shape[-1] == 3 and np.allclose(img[0, 0], img[0, 0][::-1]) else img  # BGR -> RGB if needed
        elif len(img.shape) == 3 and img.shape[0] == 3:  # CHW
            img = np.transpose(img, (1, 2, 0))
            img = img[..., ::-1]  # assume was BGR if from OpenCV
        return img.copy()

    elif isinstance(img, torch.Tensor):
        img = img.detach().cpu()
        if img.ndim == 4:  # batch
            img = img.squeeze(0)  # remove batch dim, process single image
        if img.ndim == 4:  # still batch >1 ? error
            raise ValueError("SAM2 predictor only supports single image inference")
        if img.shape[0] in [1, 3]:  # CHW
            img = img.permute(1, 2, 0)
        img = img.numpy()
        if img.max() <= 1.0:
            img = (img * 255).astype(np.uint8)
        else:
            img = img.astype(np.uint8)
        # Convert BGR to RGB if necessary (common with OpenCV-loaded images)
        if img.shape[-1] == 3:
            img = img[..., ::-1]
        return img.copy()

    elif isinstance(img, Image.Image):
        return np.array(img.convert("RGB")).copy()

    else:
        raise TypeError(f"Unsupported image type: {type(img)}")
