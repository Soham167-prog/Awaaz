import torch
import torch.nn.functional as F
from PIL import Image
import torchvision.transforms as transforms
import random
from src.models.model import PotholeSeverityModel

# Global model instance
_model = None
_device = torch.device('mps' if torch.backends.mps.is_available() else 'cuda' if torch.cuda.is_available() else 'cpu')

def load_model():
    """Load the trained model"""
    global _model
    if _model is None:
        try:
            checkpoint = torch.load('checkpoints/best.pt', map_location=_device)
            _model = PotholeSeverityModel(num_classes=4, pretrained=False)
            _model.load_state_dict(checkpoint['model_state_dict'])
            _model.to(_device)
            _model.eval()
        except Exception as e:
            print(f"Error loading model: {e}")
            _model = None
    return _model

def predict_and_generate_text(image_path):
    """
    Predict pothole severity and generate complaint text
    
    Returns:
        tuple: (severity, confidence, generated_text)
    """
    model = load_model()
    if model is None:
        return 'moderate', 0.5, "Unable to analyze image. Please try again."
    
    try:
        # Load and preprocess image
        image = Image.open(image_path).convert('RGB')
        transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        image_tensor = transform(image).unsqueeze(0).to(_device)
        
        # Get prediction
        with torch.no_grad():
            outputs = model(image_tensor)
            probabilities = F.softmax(outputs, dim=1)
            confidence, predicted = torch.max(probabilities, 1)
            
            confidence = confidence.item()
            predicted_class = predicted.item()
            
            # Class mapping: 0=none, 1=minor, 2=moderate, 3=severe
            class_names = ['none', 'minor', 'moderate', 'severe']
            predicted_label = class_names[predicted_class]
        
        # Apply confidence threshold
        confidence_threshold = 0.5
        if confidence < confidence_threshold:
            predicted_label = 'none'
        
        # Generate text based on prediction
        if predicted_label == 'none':
            generated_text = generate_none_text()
        else:
            generated_text = generate_complaint_text(predicted_label, confidence)
        
        return predicted_label, confidence, generated_text
        
    except Exception as e:
        print(f"Error processing image {image_path}: {e}")
        return 'moderate', 0.5, "Error processing image. Please try again."

def generate_none_text():
    """Generate text for images without potholes"""
    messages = [
        "This road appears to be in good condition with no visible potholes. The surface looks smooth and well-maintained.",
        "No potholes detected in this image. The road surface appears to be in satisfactory condition.",
        "The road shown in this image seems to be properly maintained with no visible damage or potholes.",
        "Good news! This road section appears to be free of potholes and in good condition.",
        "No road damage detected. The surface appears to be smooth and well-kept."
    ]
    return random.choice(messages)

def generate_complaint_text(severity, confidence):
    """Generate complaint text based on severity and confidence"""
    
    # Base templates for each severity level
    templates = {
        'minor': [
            "I've noticed a minor pothole on this road that could cause slight discomfort to drivers. While not immediately dangerous, it should be addressed to prevent further deterioration.",
            "There's a small pothole here that, while not severe, could cause minor vehicle damage over time. Early repair would be beneficial.",
            "A minor road imperfection has been identified. Though not urgent, addressing it now would prevent it from worsening.",
            "This minor pothole, while not causing immediate problems, should be monitored and repaired to maintain road quality."
        ],
        'moderate': [
            "A moderate-sized pothole has been identified on this road. This poses a risk to vehicle safety and should be repaired promptly to prevent accidents and vehicle damage.",
            "This moderate pothole requires attention as it can cause significant discomfort to drivers and potential damage to vehicles. Immediate repair is recommended.",
            "A pothole of moderate severity has been detected. This road hazard needs to be addressed soon to ensure safe driving conditions.",
            "This moderate pothole poses a clear safety concern and should be prioritized for repair to prevent accidents and vehicle damage."
        ],
        'severe': [
            "URGENT: A severe pothole has been identified that poses a serious safety hazard. This requires IMMEDIATE attention as it can cause accidents, vehicle damage, and injuries. Emergency repair is necessary.",
            "CRITICAL: This severe pothole is extremely dangerous and must be repaired immediately. It poses a high risk of accidents and serious vehicle damage. This is a safety emergency.",
            "EMERGENCY: A severe road hazard has been detected that requires immediate intervention. This pothole is dangerous and could cause serious accidents. Urgent repair needed.",
            "DANGEROUS: This severe pothole represents a critical safety issue that demands immediate action. It poses significant risk to drivers and vehicles. Emergency repair required."
        ]
    }
    
    # Select base template
    base_text = random.choice(templates[severity])
    
    # Add confidence-based qualifier
    if confidence > 0.8:
        confidence_text = " The AI analysis is highly confident in this assessment."
    elif confidence > 0.6:
        confidence_text = " The AI analysis is confident in this assessment."
    else:
        confidence_text = " The AI analysis suggests this assessment with moderate confidence."
    
    # Add location context
    location_text = " Please investigate this location and take appropriate action."
    
    return base_text + confidence_text + location_text
