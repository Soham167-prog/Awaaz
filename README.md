## Pothole Severity Classifier (Local, no API)

- Classes: `minor`, `moderate`, `severe`
- Put images into `data/potholes/train|val|test/<class>/...jpg`
- Create and activate venv: `python3 -m venv .venv && source .venv/bin/activate`
- Install deps: see below.

### Install
```
pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install streamlit opencv-python pillow numpy scikit-learn rich pyyaml
```

### Train
```
python src/train/train.py --data_dir data/potholes --epochs 15 --batch_size 32
```

### Inference
```
python src/app/predict.py --checkpoint checkpoints/best.pt --image /path/to/image.jpg
```

### Streamlit app
```
streamlit run src/app/app.py
```
