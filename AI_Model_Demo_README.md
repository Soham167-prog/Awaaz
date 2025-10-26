# AI Model Demo Jupyter Notebook

## Overview

This Jupyter notebook (`AI_Model_Demo.ipynb`) demonstrates the AI model used for automatic pothole severity detection in the Awaaz platform.

## What it Demonstrates

1. **Dataset Loading**: Loading the pothole severity dataset with 4 classes
2. **Model Architecture**: ResNet18-based model with custom classification head
3. **Model Loading**: Loading the trained model from checkpoint
4. **Prediction Testing**: Testing the model on severe pothole images

## Prerequisites

Make sure you have the following installed:

```bash
pip install torch torchvision pillow matplotlib numpy
```

## How to Run

1. Open the notebook in Jupyter:
   ```bash
   jupyter notebook AI_Model_Demo.ipynb
   ```

2. Or use JupyterLab:
   ```bash
   jupyter lab AI_Model_Demo.ipynb
   ```

3. Or use VS Code with Jupyter extension

4. Run all cells to execute the demo

## What You'll See

### Section 1: Import Libraries
- Loads PyTorch, PIL, matplotlib
- Sets up the model and dataset classes

### Section 2: Dataset Overview
- Shows total number of training samples
- Displays class distribution (Good, Minor, Moderate, Severe)
- Visualizes sample images from each class

### Section 3: Model Architecture
- Displays the ResNet18-based model structure
- Shows total number of parameters (~11M)

### Section 4: Load Trained Model
- Loads the best trained model from `checkpoints/best.pt`
- Displays training metadata (epochs, validation accuracy)

### Section 5: Test with Severe Image
- Loads a severe pothole image from test dataset
- Displays the image
- Runs inference with the model
- Shows predictions with confidence scores
- Visualizes class probabilities as bar chart
- Provides final verdict on severity

## Expected Output

```
📊 Dataset Statistics:
Total training samples: 6500+
Classes: ['good', 'minor', 'moderate', 'severe']

🏗️ Model Architecture:
ResNet18 with custom head
📊 Total parameters: 11,174,788

✅ Model loaded successfully!
Trained for 15 epochs
Best validation accuracy: 0.8500+

🔍 Prediction: SEVERE
Confidence: 0.9200

Class Probabilities:
  good: 0.0200 (2.00%)
  minor: 0.0500 (5.00%)
  moderate: 0.0100 (1.00%)
  severe: 0.9200 (92.00%)

🚨 DANGEROUS ROAD DETECTED! Requires IMMEDIATE attention.
```

## Dataset Structure

The notebook expects the dataset in this structure:

```
dataset/
├── data/
│   └── potholes/
│       ├── train/
│       │   ├── good/
│       │   ├── minor/
│       │   ├── moderate/
│       │   └── severe/
│       ├── val/
│       │   ├── good/
│       │   ├── minor/
│       │   ├── moderate/
│       │   └── severe/
│       └── test/
│           ├── good/
│           ├── minor/
│           ├── moderate/
│           └── severe/
├── plain_image _data/
│   └── train/
└── pothole_image_data/
    └── test/
```

## Model Classes

1. **good**: No potholes detected, road in good condition
2. **minor**: Small potholes, minor road damage
3. **moderate**: Moderate potholes, some road deterioration
4. **severe**: Large potholes, dangerous road conditions

## Integration with Awaaz

This AI model is integrated into the Awaaz platform to:
- Automatically detect pothole severity when users upload images
- Generate severity predictions with confidence scores
- Help prioritize repairs based on severity
- Provide visual feedback to users

## Customization

You can customize the notebook to:
- Test with your own images
- Visualize different classes
- Adjust confidence thresholds
- Compare multiple models

## Troubleshooting

**Issue**: `ModuleNotFoundError: No module named 'src'`
- **Solution**: Make sure you're running the notebook from the project root directory

**Issue**: Checkpoint not found
- **Solution**: Run training first or download the pretrained checkpoint

**Issue**: CUDA out of memory
- **Solution**: Reduce batch size or use CPU mode

## Need Help?

For questions or issues:
1. Check the main README.md
2. Review the training code in `src/train/`
3. Examine the model architecture in `src/models/model.py`

