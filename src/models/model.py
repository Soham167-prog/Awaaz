from typing import Tuple
import torch
import torch.nn as nn
import torchvision.models as models


class PotholeSeverityModel(nn.Module):
    def __init__(self, num_classes=4, pretrained=True):
        super(PotholeSeverityModel, self).__init__()
        
        # Use ResNet18 as backbone
        self.backbone = models.resnet18(weights='IMAGENET1K_V1' if pretrained else None)
        
        # Remove the final classification layer
        num_features = self.backbone.fc.in_features
        
        # Add custom classification head
        self.backbone.fc = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(num_features, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, num_classes)
        )
        
    def forward(self, x):
        return self.backbone(x)
    
    @classmethod
    def create(cls, num_classes=4, pretrained=True):
        """Factory method to create model instance"""
        return cls(num_classes=num_classes, pretrained=pretrained)
