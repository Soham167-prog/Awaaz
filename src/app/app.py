import streamlit as st
import torch
import cv2
import numpy as np
from src.models.model import PotholeSeverityModel
from src.data.dataset import CLASS_NAMES, _resize_and_pad, _to_tensor

@st.cache_resource
def load_model(checkpoint_path: str):
	device = torch.device("mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu"))
	model = PotholeSeverityModel.create(num_classes=len(CLASS_NAMES), pretrained=False)
	ckpt = torch.load(checkpoint_path, map_location=device)
	model.load_state_dict(ckpt["model_state"]) 
	model.to(device)
	model.eval()
	return model, device

st.set_page_config(page_title="Pothole Severity Classifier", page_icon="🕳️", layout="centered")
st.title("Pothole Severity Classifier")

checkpoint_path = st.text_input("Checkpoint path", value="checkpoints/best.pt")

uploaded = st.file_uploader("Upload a road image", type=["jpg","jpeg","png"])

if uploaded and checkpoint_path:
	file_bytes = np.asarray(bytearray(uploaded.read()), dtype=np.uint8)
	bgr = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
	if bgr is None:
		st.error("Invalid image")
	else:
		rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
		st.image(rgb, caption="Uploaded", use_container_width=True)
		model, device = load_model(checkpoint_path)
		proc = _resize_and_pad(rgb, 224)
		tensor = _to_tensor(proc).unsqueeze(0).to(device)
		with torch.no_grad():
			logits = model(tensor)
			probs = torch.softmax(logits, dim=1).cpu().numpy()[0]
			pred_idx = int(np.argmax(probs))
			pred_label = CLASS_NAMES[pred_idx]
			st.subheader(f"Prediction: {pred_label}")
			st.write({CLASS_NAMES[i]: float(probs[i]) for i in range(len(CLASS_NAMES))})
