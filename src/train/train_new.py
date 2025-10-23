import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, WeightedRandomSampler
from torchvision import transforms
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
from rich.console import Console
from rich.progress import track
import yaml
from datetime import datetime
import argparse

from src.models.model import PotholeSeverityModel
from src.data.dataset import PotholeDataset, get_transforms

console = Console()

class PotholeTrainer:
    def __init__(self, config):
        self.config = config
        self.device = torch.device('mps' if torch.backends.mps.is_available() else 'cuda' if torch.cuda.is_available() else 'cpu')
        console.print(f"Using device: {self.device}")
        
        # Class names for 4-class classification
        self.class_names = ['none', 'minor', 'moderate', 'severe']
        
        # Create directories
        os.makedirs('checkpoints', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        
    def prepare_data(self):
        """Prepare train/val/test splits with proper class balancing"""
        console.print("Preparing dataset...")
        
        # Load full dataset
        full_dataset = PotholeDataset(self.config['data_dir'], transform=get_transforms(train=True))
        
        # Get class distribution
        labels = [full_dataset.data[i][1] for i in range(len(full_dataset))]
        class_counts = np.bincount(labels, minlength=4)
        console.print(f"Class distribution: {class_counts}")
        
        # Check if we can use stratified splitting
        min_class_count = min(class_counts)
        if min_class_count < 2:
            console.print(f"Warning: Some classes have too few samples ({min_class_count}). Using random splitting.")
            # Use random splitting instead
            train_idx, temp_idx = train_test_split(
                range(len(full_dataset)), 
                test_size=0.3, 
                random_state=42
            )
            
            val_idx, test_idx = train_test_split(
                temp_idx, 
                test_size=0.5, 
                random_state=42
            )
        else:
            # Use stratified splitting
            train_idx, temp_idx = train_test_split(
                range(len(full_dataset)), 
                test_size=0.3, 
                stratify=labels,
                random_state=42
            )
            
            temp_labels = [full_dataset.data[i][1] for i in temp_idx]
            val_idx, test_idx = train_test_split(
                temp_idx, 
                test_size=0.5, 
                stratify=temp_labels,
                random_state=42
            )
        
        # Create datasets
        self.train_dataset = torch.utils.data.Subset(full_dataset, train_idx)
        self.val_dataset = torch.utils.data.Subset(full_dataset, val_idx)
        self.test_dataset = torch.utils.data.Subset(full_dataset, test_idx)
        
        # Calculate class weights for imbalanced data
        train_labels = [full_dataset.data[i][1] for i in train_idx]
        class_counts = np.bincount(train_labels, minlength=4)
        class_weights = 1.0 / (class_counts + 1)  # Add 1 to avoid division by zero
        class_weights = class_weights / class_weights.sum()
        
        # Create weighted sampler
        sample_weights = [class_weights[label] for label in train_labels]
        self.train_sampler = WeightedRandomSampler(sample_weights, len(sample_weights))
        
        # Create dataloaders
        self.train_loader = DataLoader(
            self.train_dataset, 
            batch_size=self.config['batch_size'],
            sampler=self.train_sampler,
            num_workers=4,
            pin_memory=True
        )
        
        self.val_loader = DataLoader(
            self.val_dataset,
            batch_size=self.config['batch_size'],
            shuffle=False,
            num_workers=4,
            pin_memory=True
        )
        
        self.test_loader = DataLoader(
            self.test_dataset,
            batch_size=self.config['batch_size'],
            shuffle=False,
            num_workers=4,
            pin_memory=True
        )
        
        console.print(f"Train: {len(self.train_dataset)}, Val: {len(self.val_dataset)}, Test: {len(self.test_dataset)}")
        console.print(f"Class distribution: {class_counts}")
        
    def create_model(self):
        """Create and initialize the model"""
        console.print("Creating model...")
        
        self.model = PotholeSeverityModel(num_classes=4, pretrained=False)
        self.model.to(self.device)
        
        # Loss function with class weights
        train_labels = [self.train_dataset.dataset.data[i][1] for i in self.train_dataset.indices]
        class_counts = np.bincount(train_labels, minlength=4)
        class_weights = torch.FloatTensor(1.0 / (class_counts + 1)).to(self.device)
        self.criterion = nn.CrossEntropyLoss(weight=class_weights)
        
        # Optimizer
        self.optimizer = optim.AdamW(
            self.model.parameters(),
            lr=self.config['learning_rate'],
            weight_decay=self.config['weight_decay']
        )
        
        # Learning rate scheduler
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, 
            mode='min', 
            factor=0.5, 
            patience=5
        )
        
    def train_epoch(self, epoch):
        """Train for one epoch"""
        self.model.train()
        total_loss = 0
        correct = 0
        total = 0
        
        for batch_idx, (data, target) in enumerate(track(self.train_loader, description=f"Epoch {epoch}")):
            data, target = data.to(self.device), target.to(self.device)
            
            self.optimizer.zero_grad()
            output = self.model(data)
            loss = self.criterion(output, target)
            loss.backward()
            self.optimizer.step()
            
            total_loss += loss.item()
            pred = output.argmax(dim=1, keepdim=True)
            correct += pred.eq(target.view_as(pred)).sum().item()
            total += target.size(0)
            
        accuracy = 100. * correct / total
        avg_loss = total_loss / len(self.train_loader)
        
        return avg_loss, accuracy
    
    def validate(self, loader, split_name="Validation"):
        """Validate the model"""
        self.model.eval()
        total_loss = 0
        correct = 0
        total = 0
        all_preds = []
        all_targets = []
        
        with torch.no_grad():
            for data, target in loader:
                data, target = data.to(self.device), target.to(self.device)
                output = self.model(data)
                loss = self.criterion(output, target)
                
                total_loss += loss.item()
                pred = output.argmax(dim=1, keepdim=True)
                correct += pred.eq(target.view_as(pred)).sum().item()
                total += target.size(0)
                
                all_preds.extend(pred.cpu().numpy().flatten())
                all_targets.extend(target.cpu().numpy())
        
        accuracy = 100. * correct / total
        avg_loss = total_loss / len(loader)
        
        console.print(f"{split_name} - Loss: {avg_loss:.4f}, Accuracy: {accuracy:.2f}%")
        
        return avg_loss, accuracy, all_preds, all_targets
    
    def save_checkpoint(self, epoch, loss, accuracy, is_best=False):
        """Save model checkpoint"""
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'loss': loss,
            'accuracy': accuracy,
            'config': self.config
        }
        
        # Save latest checkpoint
        torch.save(checkpoint, 'checkpoints/latest.pt')
        
        # Save best checkpoint
        if is_best:
            torch.save(checkpoint, 'checkpoints/best.pt')
            console.print(f"New best model saved! Accuracy: {accuracy:.2f}%")
    
    def plot_confusion_matrix(self, y_true, y_pred, title, save_path):
        """Plot and save confusion matrix"""
        cm = confusion_matrix(y_true, y_pred)
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                   xticklabels=self.class_names, yticklabels=self.class_names)
        plt.title(title)
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        plt.tight_layout()
        plt.savefig(save_path)
        plt.close()
    
    def train(self):
        """Main training loop"""
        console.print("Starting training...")
        
        best_val_loss = float('inf')
        best_val_accuracy = 0
        
        for epoch in range(1, self.config['epochs'] + 1):
            # Train
            train_loss, train_acc = self.train_epoch(epoch)
            
            # Validate
            val_loss, val_acc, val_preds, val_targets = self.validate(self.val_loader)
            
            # Update learning rate
            self.scheduler.step(val_loss)
            
            # Log progress
            console.print(f"Epoch {epoch}: Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}%")
            
            # Save checkpoint
            is_best = val_acc > best_val_accuracy
            if is_best:
                best_val_accuracy = val_acc
                best_val_loss = val_loss
            
            self.save_checkpoint(epoch, val_loss, val_acc, is_best)
            
            # Plot confusion matrix every 10 epochs
            if epoch % 10 == 0:
                self.plot_confusion_matrix(
                    val_targets, val_preds, 
                    f'Validation Confusion Matrix - Epoch {epoch}',
                    f'logs/confusion_matrix_epoch_{epoch}.png'
                )
        
        # Final evaluation on test set
        console.print("Evaluating on test set...")
        test_loss, test_acc, test_preds, test_targets = self.validate(self.test_loader, "Test")
        
        # Generate final reports
        self.plot_confusion_matrix(
            test_targets, test_preds,
            'Test Confusion Matrix - Final',
            'logs/final_confusion_matrix.png'
        )
        
        # Classification report
        report = classification_report(
            test_targets, test_preds, 
            target_names=self.class_names, 
            output_dict=True
        )
        
        console.print("Final Test Results:")
        console.print(f"Accuracy: {test_acc:.2f}%")
        console.print(f"Loss: {test_loss:.4f}")
        
        # Save results
        with open('logs/final_results.yaml', 'w') as f:
            yaml.dump({
                'test_accuracy': test_acc,
                'test_loss': test_loss,
                'classification_report': report,
                'config': self.config
            }, f, default_flow_style=False)

def main():
    parser = argparse.ArgumentParser(description='Train Pothole Severity Classification Model')
    parser.add_argument('--config', type=str, default='config.yaml', help='Path to config file')
    parser.add_argument('--data_dir', type=str, default='.', help='Path to data directory')
    parser.add_argument('--epochs', type=int, default=50, help='Number of epochs')
    parser.add_argument('--batch_size', type=int, default=32, help='Batch size')
    parser.add_argument('--learning_rate', type=float, default=1e-4, help='Learning rate')
    parser.add_argument('--weight_decay', type=float, default=1e-4, help='Weight decay')
    
    args = parser.parse_args()
    
    # Load config or use defaults
    if os.path.exists(args.config):
        with open(args.config, 'r') as f:
            config = yaml.safe_load(f)
    else:
        config = {
            'data_dir': args.data_dir,
            'epochs': args.epochs,
            'batch_size': args.batch_size,
            'learning_rate': args.learning_rate,
            'weight_decay': args.weight_decay
        }
    
    # Create trainer and start training
    trainer = PotholeTrainer(config)
    trainer.prepare_data()
    trainer.create_model()
    trainer.train()

if __name__ == '__main__':
    main()
