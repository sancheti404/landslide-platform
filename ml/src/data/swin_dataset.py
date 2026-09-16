"""
PyTorch Dataset and DataLoaders for Swin Transformer satellite visual risk branch.
"""

from pathlib import Path
import pandas as pd
from PIL import Image
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms


# ImageNet statistics for pretrained Swin
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def get_train_transforms(image_size=224):
    """
    Spatial augmentations for training set only.
    Preserves realistic satellite physical appearance (flips and discrete 90-deg rotations).
    """
    return transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomVerticalFlip(p=0.5),
        transforms.RandomRotation(degrees=(0, 0)),  # Controlled geometric stability
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])


def get_eval_transforms(image_size=224):
    """
    Deterministic preprocessing for validation and held-out test sets.
    """
    return transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])


class Sentinel2PatchDataset(Dataset):
    """
    Loads Sentinel-2 RGB patches and aligns them with sample_id and binary landslide ground-truth.
    """

    def __init__(self, metadata_df, patches_dir, transform=None):
        self.metadata = metadata_df.reset_index(drop=True)
        self.patches_dir = Path(patches_dir)
        self.transform = transform

    def __len__(self):
        return len(self.metadata)

    def __getitem__(self, idx):
        row = self.metadata.iloc[idx]
        sample_id = row["sample_id"]
        label = float(row["landslide"])

        img_path = self.patches_dir / f"{sample_id}.png"
        if not img_path.exists():
            raise FileNotFoundError(f"Image patch not found for sample: {img_path}")

        image = Image.open(img_path).convert("RGB")

        if self.transform:
            image_tensor = self.transform(image)
        else:
            image_tensor = transforms.ToTensor()(image)

        return {
            "image": image_tensor,
            "label": torch.tensor(label, dtype=torch.float32),
            "sample_id": sample_id,
            "latitude": float(row["latitude"]),
            "longitude": float(row["longitude"]),
        }


def create_dataloaders(
    train_df,
    val_df,
    test_df,
    patches_dir="ml/data/processed/patches",
    batch_size=32,
    num_workers=0,
    image_size=224
):
    """
    Create PyTorch DataLoaders for Train, Validation, and Test splits.
    """
    train_transform = get_train_transforms(image_size)
    eval_transform = get_eval_transforms(image_size)

    train_dataset = Sentinel2PatchDataset(train_df, patches_dir, transform=train_transform)
    val_dataset = Sentinel2PatchDataset(val_df, patches_dir, transform=eval_transform)
    test_dataset = Sentinel2PatchDataset(test_df, patches_dir, transform=eval_transform)

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available()
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available()
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available()
    )

    return train_loader, val_loader, test_loader
