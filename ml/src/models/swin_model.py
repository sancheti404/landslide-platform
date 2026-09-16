"""
Swin Transformer model architecture for Landslide Satellite Visual Risk Branch.
Based on torchvision Swin-Tiny with custom transfer-learning binary classification head.
"""

import torch
import torch.nn as nn
from torchvision.models import swin_t, Swin_T_Weights


class SwinLandslideClassifier(nn.Module):
    """
    Swin-Tiny Transformer model for satellite visual landslide risk estimation.
    Outputs continuous probability P(satellite visual evidence indicates landslide).
    """

    def __init__(self, pretrained=True, dropout_rate=0.3):
        super().__init__()
        self.dropout_rate = dropout_rate
        self.pretrained = pretrained

        if pretrained:
            weights = Swin_T_Weights.DEFAULT
            self.backbone = swin_t(weights=weights)
        else:
            self.backbone = swin_t(weights=None)

        in_features = self.backbone.head.in_features  # 768 for Swin-T

        # Replace 1000-class head with binary risk classification head
        self.backbone.head = nn.Sequential(
            nn.Dropout(p=dropout_rate),
            nn.Linear(in_features, 1)
        )

    def freeze_backbone(self):
        """Freeze all layers except the classification head."""
        for name, param in self.backbone.named_parameters():
            if "head" not in name:
                param.requires_grad = False
            else:
                param.requires_grad = True

    def unfreeze_all(self):
        """Unfreeze all parameters for end-to-end fine-tuning."""
        for param in self.parameters():
            param.requires_grad = True

    def unfreeze_later_stages(self):
        """
        Unfreeze later Swin stages (stage 3 and stage 4/features.7) while keeping
        early stem layers frozen to preserve fundamental spatial feature extractors.
        """
        for name, param in self.backbone.named_parameters():
            # In torchvision swin_t: features has blocks 0 to 7.
            # features[5] is stage 3, features[7] is stage 4.
            if "features.5" in name or "features.6" in name or "features.7" in name or "head" in name or "norm" in name:
                param.requires_grad = True
            else:
                param.requires_grad = False

    def forward(self, x):
        """Returns raw logits of shape (B, 1)."""
        return self.backbone(x)

    def predict_proba(self, x):
        """Returns sigmoid risk probabilities of shape (B, 1)."""
        logits = self.forward(x)
        return torch.sigmoid(logits)
