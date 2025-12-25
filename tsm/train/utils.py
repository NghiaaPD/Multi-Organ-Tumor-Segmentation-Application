from torch.utils.data import Dataset

import json
from PIL import Image
import numpy as np

class Dataloader(Dataset):
    def __init__(self, data_path, transform=None, mask_transform=None):
        with open(data_path, 'r') as f:
            self.entries = json.load(f)
        self.transform = transform
        self.mask_transform = mask_transform

    def __len__(self):
        return len(self.entries)

    def __getitem__(self, idx):
        entry = self.entries[idx]
        img = Image.open(entry['image']).convert('RGB')
        mask = Image.open(entry['label_mask'])
        if self.transform:
            img = self.transform(img)
        if self.mask_transform:
            mask = self.mask_transform(mask)
        else:
            mask = np.array(mask)

        return np.array(img), mask  
    
class Dataprocessor:
    def __init__(self, img_size=(1024, 1024), normalize=False, to_float32=False):
        # Default img_size lớn hơn cho SAM 2 (tối đa 1024)
        self.img_size = img_size
        self.normalize = normalize  # Default False cho SAM 2 (giữ uint8)
        self.to_float32 = to_float32  # Default False

    def resize(self, img, mask=None):
        img = img.resize(self.img_size, Image.BILINEAR)
        if mask is not None:
            mask = mask.resize(self.img_size, Image.NEAREST)
            return img, mask
        return img

    def to_numpy(self, img, mask=None):
        img = np.array(img)
        if mask is not None:
            mask = np.array(mask)
            return img, mask
        return img

    def normalize_img(self, img):
        img = img.astype(np.float32)
        img = img / 255.0
        return img

    def process(self, img, mask=None):
        # Resize
        img, mask = self.resize(img, mask) if mask is not None else (self.resize(img), None)
        # To numpy
        img, mask = self.to_numpy(img, mask) if mask is not None else (self.to_numpy(img), None)
        # Normalize chỉ nếu cần (không khuyến nghị cho SAM 2 input)
        if self.normalize:
            img = self.normalize_img(img)

        if self.to_float32:
            img = img.astype(np.float32)
        return (img, mask) if mask is not None else img