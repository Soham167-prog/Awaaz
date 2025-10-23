import os
import csv
import random
from typing import List, Dict

import streamlit as st
from PIL import Image

SOURCE_DIR = "pothole_image_data/Pothole_Image_Data"
LABELS_DIR = "labels"
LABELS_CSV = os.path.join(LABELS_DIR, "labels.csv")
CLASSES = ["minor", "moderate", "severe"]

os.makedirs(LABELS_DIR, exist_ok=True)


def load_image_paths() -> List[str]:
	valid_ext = (".jpg", ".jpeg", ".png")
	files = [os.path.join(SOURCE_DIR, f) for f in os.listdir(SOURCE_DIR) if f.lower().endswith(valid_ext)]
	files.sort()
	return files


def load_labels() -> Dict[str, str]:
	labels = {}
	if os.path.isfile(LABELS_CSV):
		with open(LABELS_CSV, "r", newline="") as f:
			reader = csv.reader(f)
			for row in reader:
				if len(row) == 2:
					labels[row[0]] = row[1]
	return labels


def save_label(path: str, label: str) -> None:
	labels = load_labels()
	labels[path] = label
	with open(LABELS_CSV, "w", newline="") as f:
		writer = csv.writer(f)
		for k, v in labels.items():
			writer.writerow([k, v])


st.set_page_config(page_title="Pothole Labeler", page_icon="🕳️", layout="wide")
st.title("Pothole Severity Labeler")

all_paths = load_image_paths()
labels = load_labels()

unlabeled = [p for p in all_paths if p not in labels]
labeled_count = len(all_paths) - len(unlabeled)

st.sidebar.write(f"Total images: {len(all_paths)}")
st.sidebar.write(f"Labeled: {labeled_count}")
st.sidebar.write(f"Remaining: {len(unlabeled)}")

shuffle = st.sidebar.checkbox("Shuffle", value=True)
if shuffle:
	random.seed(42)
	random.shuffle(unlabeled)

cols = st.columns(2)

if unlabeled:
	current = unlabeled[0]
	img = Image.open(current).convert("RGB")
	cols[0].image(img, caption=os.path.basename(current), use_container_width=True)
	cols[1].markdown("### Assign label")
	for c in CLASSES:
		if cols[1].button(c.capitalize(), use_container_width=True):
			save_label(current, c)
			st.rerun()

	if cols[1].button("Skip", use_container_width=True):
		# mark as skipped with special tag
		save_label(current, "skip")
		st.rerun()
else:
	st.success("All images labeled! You can export the split now.")
	st.info("Run: python src/utils/export_split.py --labels labels/labels.csv --out_dir data/potholes --val_ratio 0.15 --test_ratio 0.15")
