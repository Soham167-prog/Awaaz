import torch
import torch.nn.functional as F
from PIL import Image
import torchvision.transforms as transforms
import numpy as np
from src.models.model import PotholeSeverityModel

class PotholePredictor:
    def __init__(self, checkpoint_path='checkpoints/best.pt'):
        self.device = torch.device('mps' if torch.backends.mps.is_available() else 'cuda' if torch.cuda.is_available() else 'cpu')
        self.class_names = ['none', 'minor', 'moderate', 'severe']
        self.confidence_threshold = 0.5  # Minimum confidence to make a prediction
        
        # Load model
        self.model = self._load_model(checkpoint_path)
        
        # Define transforms
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
    
    def _load_model(self, checkpoint_path):
        """Load the trained model from checkpoint"""
        try:
            checkpoint = torch.load(checkpoint_path, map_location=self.device)
            model = PotholeSeverityModel(num_classes=4, pretrained=False)
            model.load_state_dict(checkpoint['model_state_dict'])
            model.to(self.device)
            model.eval()
            return model
        except Exception as e:
            print(f"Error loading model: {e}")
            return None
    
    def predict(self, image_path):
        """
        Predict pothole severity from image
        
        Returns:
            tuple: (prediction, confidence, is_valid_image)
            - prediction: 'none', 'minor', 'moderate', 'severe', or 'invalid'
            - confidence: confidence score (0-1)
            - is_valid_image: boolean indicating if image was processed successfully
        """
        if self.model is None:
            return 'invalid', 0.0, False
        
        try:
            # Load and preprocess image
            image = Image.open(image_path).convert('RGB')
            image_tensor = self.transform(image).unsqueeze(0).to(self.device)
            
            # Get prediction
            with torch.no_grad():
                outputs = self.model(image_tensor)
                probabilities = F.softmax(outputs, dim=1)
                confidence, predicted = torch.max(probabilities, 1)
                
                confidence = confidence.item()
                predicted_class = predicted.item()
                predicted_label = self.class_names[predicted_class]
            
            # Apply confidence threshold
            if confidence < self.confidence_threshold:
                return 'none', confidence, True
            
            # Special handling for 'none' class (good road)
            if predicted_label == 'none':
                return 'none', confidence, True
            
            return predicted_label, confidence, True
            
        except Exception as e:
            print(f"Error processing image {image_path}: {e}")
            return 'invalid', 0.0, False
    
    def predict_batch(self, image_paths):
        """Predict for multiple images"""
        results = []
        for image_path in image_paths:
            prediction, confidence, is_valid = self.predict(image_path)
            results.append({
                'image_path': image_path,
                'prediction': prediction,
                'confidence': confidence,
                'is_valid': is_valid
            })
        return results

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Predict pothole severity from image')
    parser.add_argument('image_path', help='Path to image file')
    parser.add_argument('--checkpoint', default='checkpoints/best.pt', help='Path to model checkpoint')
    parser.add_argument('--threshold', type=float, default=0.5, help='Confidence threshold')
    
    args = parser.parse_args()
    
    predictor = PotholePredictor(args.checkpoint)
    predictor.confidence_threshold = args.threshold
    
    prediction, confidence, is_valid = predictor.predict(args.image_path)
    
    if is_valid:
        if prediction == 'none':
            print(f"✅ No pothole detected (confidence: {confidence:.3f})")
            print("This appears to be a good road surface.")
        elif prediction == 'invalid':
            print("❌ Invalid image or processing error")
        else:
            print(f"🚧 Pothole detected: {prediction.upper()} severity (confidence: {confidence:.3f})")
    else:
        print("❌ Failed to process image")

if __name__ == '__main__':
    main()
