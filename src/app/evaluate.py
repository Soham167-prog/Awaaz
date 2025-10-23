import argparse
import os
import torch
from torch.utils.data import DataLoader
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix

from src.data.dataset import PotholeImageDataset, CLASS_NAMES
from src.models.model import PotholeSeverityModel


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("--data_dir", default="data/potholes")
	parser.add_argument("--checkpoint", default="checkpoints/best.pt")
	args = parser.parse_args()

	device = torch.device("mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu"))
	ds = PotholeImageDataset(args.data_dir, split="test", image_size=224, augment=False)
	loader = DataLoader(ds, batch_size=32, shuffle=False, num_workers=2)

	model = PotholeSeverityModel.create(num_classes=len(CLASS_NAMES), pretrained=False)
	ckpt = torch.load(args.checkpoint, map_location=device)
	model.load_state_dict(ckpt["model_state"]) 
	model.to(device)
	model.eval()

	all_preds, all_labels = [], []
	with torch.no_grad():
		for images, labels in loader:
			images = images.to(device)
			logits = model(images)
			preds = logits.argmax(dim=1).cpu().tolist()
			all_preds.extend(preds)
			all_labels.extend(labels.tolist())

	acc = accuracy_score(all_labels, all_preds)
	print(f"Accuracy: {acc:.4f}")
	print("Classification report:")
	print(classification_report(all_labels, all_preds, target_names=CLASS_NAMES, digits=4))
	print("Confusion matrix:")
	print(confusion_matrix(all_labels, all_preds))


if __name__ == "__main__":
	main()
