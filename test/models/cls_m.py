from loguru import logger
from PIL import Image
import torch
import torchvision.transforms as T
from tsm.model.classification_model import builder
from tsm.model.classification_model.fastvit.fastvit_predictor import FastViTPredictor
import os

def main():
    model_config = "fastvit_ma36.yaml"
    ckpt_path = "output/20251226-024026-fastvit_ma36-256/model_best.pth.tar"
    img_path = "data/MOTSA_classification/validation/liver/img87.jpeg"
    if not os.path.exists(img_path):
        img = Image.new("RGB", (256, 256), color=(123, 222, 111))
        img.save(img_path)
    else:
        img = Image.open(img_path).convert("RGB")

    transform = T.Compose([
        T.Resize((256, 256)),
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    input_tensor = transform(img).unsqueeze(0)

    logger.info(f"Testing model: {model_config}")
    model = builder.build_fastvit(
        config_file=model_config,
        ckpt_path=ckpt_path,
        device="cuda",
        mode="eval"
    )
    predictor = FastViTPredictor(model, device="cuda")
    predictor.set_image(input_tensor)
    output = predictor.predict()
    import torch.nn.functional as F
    logger.info(f"Output shape: {output.shape}")
    logger.info(f"Output logits: {output}")
    probs = F.softmax(output, dim=1)
    logger.info(f"Output probs (softmax): {probs.cpu().numpy()}")
    pred_class = probs.argmax(dim=1).item()
    logger.info(f"Predicted class: {pred_class}")
    logger.success(f"Model {model_config} predict test passed!")

if __name__ == "__main__":
    main()
