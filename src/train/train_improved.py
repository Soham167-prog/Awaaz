import os
import argparse
from typing import Dict, List
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, WeightedRandomSampler
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

from src.data.dataset import PotholeImageDataset, CLASS_NAMES
from src.models.model import PotholeSeverityModel


def accuracy(logits: torch.Tensor, targets: torch.Tensor) -> float:
    preds = logits.argmax(dim=1)
    return (preds == targets).float().mean().item()


def save_checkpoint(state: Dict, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    torch.save(state, path)


def compute_class_weights(labels: List[int], num_classes: int) -> torch.Tensor:
    counts = [0] * num_classes
    for y in labels:
        counts[y] += 1
    total = sum(counts)
    # inverse frequency weights
    weights = [total / (c if c > 0 else 1) for c in counts]
    # normalize to sum to num_classes for stability
    sum_w = sum(weights)
    weights = [w * (num_classes / sum_w) for w in weights]
    return torch.tensor(weights, dtype=torch.float32)


def build_weighted_sampler(labels: List[int]) -> WeightedRandomSampler:
    # per-sample weights are inverse of class frequency
    from collections import Counter
    ctr = Counter(labels)
    weights_per_class = {c: 1.0 / ctr[c] for c in ctr}
    weights = [weights_per_class[y] for y in labels]
    return WeightedRandomSampler(weights, num_samples=len(labels), replacement=True)


def train_one_epoch(model, loader, criterion, optimizer, device):
    model.train()
    running_loss = 0.0
    running_acc = 0.0
    n = 0
    for images, labels in loader:
        images = images.to(device)
        labels = labels.to(device)
        optimizer.zero_grad()
        logits = model(images)
        loss = criterion(logits, labels)
        loss.backward()
        optimizer.step()
        running_loss += loss.item() * images.size(0)
        running_acc += accuracy(logits.detach(), labels) * images.size(0)
        n += images.size(0)
    return running_loss / n, running_acc / n


def evaluate(model, loader, criterion, device, class_names=None):
    model.eval()
    running_loss = 0.0
    running_acc = 0.0
    n = 0
    all_preds = []
    all_labels = []
    
    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device)
            labels = labels.to(device)
            logits = model(images)
            loss = criterion(logits, labels)
            running_loss += loss.item() * images.size(0)
            running_acc += accuracy(logits, labels) * images.size(0)
            n += images.size(0)
            
            # Collect predictions for detailed evaluation
            preds = logits.argmax(dim=1)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
    
    # Generate classification report
    if class_names:
        print("\nClassification Report:")
        print(classification_report(all_labels, all_preds, target_names=class_names))
        
        # Generate confusion matrix
        cm = confusion_matrix(all_labels, all_preds)
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                   xticklabels=class_names, yticklabels=class_names)
        plt.title('Confusion Matrix')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        plt.tight_layout()
        plt.savefig('logs/confusion_matrix_improved.png', dpi=150, bbox_inches='tight')
        plt.close()
    
    return running_loss / n, running_acc / n


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", type=str, default=".")
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--checkpoint_dir", type=str, default="checkpoints")
    parser.add_argument("--resume", type=str, default="")
    parser.add_argument("--no_pretrained", action="store_true")
    parser.add_argument("--no_balanced", action="store_true", help="Disable class-balanced sampling and loss")
    args = parser.parse_args()

    device = torch.device("mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu"))
    print(f"Using device: {device}")

    # Create datasets
    train_ds = PotholeImageDataset(args.data_dir, split="train", image_size=224, augment=True)
    val_ds = PotholeImageDataset(args.data_dir, split="val", image_size=224, augment=False)
    test_ds = PotholeImageDataset(args.data_dir, split="test", image_size=224, augment=False)

    # Collect labels for balancing
    train_labels = [lbl for (_, lbl) in train_ds.samples]

    if args.no_balanced:
        train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=2)
        class_weights = torch.ones(len(CLASS_NAMES), dtype=torch.float32)
    else:
        sampler = build_weighted_sampler(train_labels)
        train_loader = DataLoader(train_ds, batch_size=args.batch_size, sampler=sampler, num_workers=2)
        class_weights = compute_class_weights(train_labels, num_classes=len(CLASS_NAMES))

    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, num_workers=2)
    test_loader = DataLoader(test_ds, batch_size=args.batch_size, shuffle=False, num_workers=2)

    model = PotholeSeverityModel.create(num_classes=len(CLASS_NAMES), pretrained=not args.no_pretrained)
    model.to(device)

    criterion = nn.CrossEntropyLoss(weight=class_weights.to(device))
    optimizer = AdamW(model.parameters(), lr=args.lr)
    scheduler = CosineAnnealingLR(optimizer, T_max=args.epochs)

    best_val_acc = 0.0
    start_epoch = 0
    if args.resume and os.path.isfile(args.resume):
        ckpt = torch.load(args.resume, map_location=device)
        model.load_state_dict(ckpt["model_state"]) 
        optimizer.load_state_dict(ckpt["optimizer_state"]) 
        scheduler.load_state_dict(ckpt["scheduler_state"]) 
        start_epoch = ckpt.get("epoch", 0) + 1
        best_val_acc = ckpt.get("best_val_acc", 0.0)
        print(f"Resumed from {args.resume} at epoch {start_epoch}")

    print(f"Training with {len(CLASS_NAMES)} classes: {CLASS_NAMES}")
    print(f"Class weights: {class_weights}")

    for epoch in range(start_epoch, args.epochs):
        tr_loss, tr_acc = train_one_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_acc = evaluate(model, val_loader, criterion, device)

        scheduler.step()

        print(f"Epoch {epoch+1}/{args.epochs} | Train Loss {tr_loss:.4f} Acc {tr_acc:.4f} | Val Loss {val_loss:.4f} Acc {val_acc:.4f}")

        state = {
            "epoch": epoch,
            "model_state": model.state_dict(),
            "optimizer_state": optimizer.state_dict(),
            "scheduler_state": scheduler.state_dict(),
            "best_val_acc": best_val_acc,
            "class_names": CLASS_NAMES,
        }
        save_checkpoint(state, os.path.join(args.checkpoint_dir, "last.pt"))

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            state["best_val_acc"] = best_val_acc
            save_checkpoint(state, os.path.join(args.checkpoint_dir, "best.pt"))
            print(f"New best validation accuracy: {best_val_acc:.4f}")

    print("Training complete. Best Val Acc:", best_val_acc)
    
    # Final evaluation on test set
    print("\nEvaluating on test set...")
    test_loss, test_acc = evaluate(model, test_loader, criterion, device, CLASS_NAMES)
    print(f"Test Accuracy: {test_acc:.4f}")


if __name__ == "__main__":
    main()

