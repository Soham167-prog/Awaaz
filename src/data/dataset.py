import os
import torch
from torch.utils.data import Dataset
from PIL import Image
import torchvision.transforms as transforms
from typing import Tuple, Optional

class PotholeDataset(Dataset):
    def __init__(self, data_dir: str, transform: Optional[transforms.Compose] = None):
        """
        Dataset for pothole severity classification
        
        Args:
            data_dir: Root directory containing train/test folders
            transform: Optional transforms to apply
        """
        self.data_dir = data_dir
        self.transform = transform or self._get_default_transforms()
        
        # Class mapping: 0=none, 1=minor, 2=moderate, 3=severe
        self.class_names = ['none', 'minor', 'moderate', 'severe']
        self.class_to_idx = {name: idx for idx, name in enumerate(self.class_names)}
        
        # Load data paths and labels
        self.data = []
        self._load_data()
        
    def _load_data(self):
        """Load image paths and labels from the dataset structure"""
        # Load pothole images (minor, moderate, severe)
        pothole_dir = os.path.join(self.data_dir, 'pothole_image_data')
        if os.path.exists(pothole_dir):
            for split in ['train', 'test']:
                split_dir = os.path.join(pothole_dir, split)
                if os.path.exists(split_dir):
                    for img_name in os.listdir(split_dir):
                        if img_name.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                            img_path = os.path.join(split_dir, img_name)
                            # Determine severity from filename or use moderate as default
                            severity = self._extract_severity_from_filename(img_name)
                            if severity in self.class_to_idx:
                                self.data.append((img_path, self.class_to_idx[severity]))
        
        # Load plain road images (none class)
        plain_dir = os.path.join(self.data_dir, 'plain_image _data')
        if os.path.exists(plain_dir):
            for split in ['train', 'test']:
                split_dir = os.path.join(plain_dir, split)
                if os.path.exists(split_dir):
                    for img_name in os.listdir(split_dir):
                        if img_name.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                            img_path = os.path.join(split_dir, img_name)
                            self.data.append((img_path, self.class_to_idx['none']))
    
    def _extract_severity_from_filename(self, filename: str) -> str:
        """Extract severity from filename based on keywords"""
        filename_lower = filename.lower()
        
        if any(word in filename_lower for word in ['severe', 'critical', 'dangerous', 'deep']):
            return 'severe'
        elif any(word in filename_lower for word in ['moderate', 'medium', 'mod']):
            return 'moderate'
        elif any(word in filename_lower for word in ['minor', 'small', 'light']):
            return 'minor'
        else:
            # Default to moderate if no clear indication
            return 'moderate'
    
    def _get_default_transforms(self) -> transforms.Compose:
        """Get default transforms for training"""
        return transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomRotation(degrees=10),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
    
    def __len__(self) -> int:
        return len(self.data)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        img_path, label = self.data[idx]
        
        try:
            # Load and convert image to RGB
            image = Image.open(img_path).convert('RGB')
            
            # Apply transforms
            if self.transform:
                image = self.transform(image)
            
            # Ensure tensor is float32 for MPS compatibility
            if image.dtype != torch.float32:
                image = image.float()
            
            return image, label
            
        except Exception as e:
            print(f"Error loading image {img_path}: {e}")
            # Return a placeholder image if loading fails
            placeholder = torch.zeros(3, 224, 224, dtype=torch.float32)
            return placeholder, label

def get_transforms(train: bool = True) -> transforms.Compose:
    """Get transforms for training or validation"""
    if train:
        return transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomRotation(degrees=10),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
    else:
        return transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
