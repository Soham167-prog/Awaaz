import os
import csv
import argparse
from typing import Tuple
import cv2
import numpy as np

SOURCE_DIR = "pothole_image_data/Pothole_Image_Data"
LABELS_DIR = "labels"
LABELS_CSV = os.path.join(LABELS_DIR, "labels.csv")

os.makedirs(LABELS_DIR, exist_ok=True)


def compute_features(img: np.ndarray) -> Tuple[float, float]:
	gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
	h, w = gray.shape
	edges = cv2.Canny(gray, 100, 200)
	edge_density = float(edges.sum()) / (255.0 * h * w)
	# Use Otsu to pick a robust threshold for dark region
	_, thr = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
	dark_ratio = (gray < thr * 0.8).mean()
	return edge_density, dark_ratio


def assign_label(edge_density: float, dark_ratio: float) -> str:
	severity = 0.55 * dark_ratio + 0.45 * edge_density
	if severity < 0.12:
		return "minor"
	elif severity < 0.28:
		return "moderate"
	else:
		return "severe"


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("--source_dir", default=SOURCE_DIR)
	parser.add_argument("--out_csv", default=LABELS_CSV)
	args = parser.parse_args()

	valid_ext = (".jpg", ".jpeg", ".png")
	files = [os.path.join(args.source_dir, f) for f in os.listdir(args.source_dir) if f.lower().endswith(valid_ext)]
	files.sort()

	with open(args.out_csv, "w", newline="") as f:
		writer = csv.writer(f)
		for i, path in enumerate(files, 1):
			img = cv2.imread(path)
			if img is None:
				continue
			ed, dr = compute_features(img)
			label = assign_label(ed, dr)
			writer.writerow([path, label])
			if i % 50 == 0:
				print(f"Labeled {i}/{len(files)}")
	print("Auto-labeling complete:", args.out_csv)


if __name__ == "__main__":
	main()
