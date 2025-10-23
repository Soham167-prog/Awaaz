import os
import csv
import shutil
import argparse
from collections import defaultdict
from typing import Dict, List, Tuple


def read_labels(csv_path: str) -> Dict[str, str]:
	labels = {}
	with open(csv_path, "r", newline="") as f:
		reader = csv.reader(f)
		for row in reader:
			if len(row) != 2:
				continue
			path, label = row
			if label == "skip":
				continue
			labels[path] = label
	return labels


def stratified_split(items: List[Tuple[str, str]], val_ratio: float, test_ratio: float):
	by_class = defaultdict(list)
	for path, label in items:
		by_class[label].append(path)

	train, val, test = [], [], []
	for label, paths in by_class.items():
		paths.sort()
		n = len(paths)
		n_val = int(n * val_ratio)
		n_test = int(n * test_ratio)
		val.extend([(p, label) for p in paths[:n_val]])
		test.extend([(p, label) for p in paths[n_val:n_val + n_test]])
		train.extend([(p, label) for p in paths[n_val + n_test:]])
	return train, val, test


def copy_items(items: List[Tuple[str, str]], out_dir: str, split: str) -> None:
	for path, label in items:
		dst_dir = os.path.join(out_dir, split, label)
		os.makedirs(dst_dir, exist_ok=True)
		shutil.copy2(path, os.path.join(dst_dir, os.path.basename(path)))


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("--labels", required=True)
	parser.add_argument("--out_dir", default="data/potholes")
	parser.add_argument("--val_ratio", type=float, default=0.15)
	parser.add_argument("--test_ratio", type=float, default=0.15)
	args = parser.parse_args()

	labels = read_labels(args.labels)
	items = list(labels.items())
	train, val, test = stratified_split(items, args.val_ratio, args.test_ratio)

	copy_items(train, args.out_dir, "train")
	copy_items(val, args.out_dir, "val")
	copy_items(test, args.out_dir, "test")
	print("Exported:")
	print(f"  train: {len(train)}")
	print(f"  val:   {len(val)}")
	print(f"  test:  {len(test)}")


if __name__ == "__main__":
	main()
