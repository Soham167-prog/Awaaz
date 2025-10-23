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
            import os
            checkpoint_path = 'checkpoints/best.pt'
            if not os.path.exists(checkpoint_path):
                print(f"Model checkpoint not found at {checkpoint_path}")
                return None
            
            checkpoint = torch.load(checkpoint_path, map_location=_device)
            _model = PotholeSeverityModel(num_classes=4, pretrained=False)
            _model.load_state_dict(checkpoint['model_state'])
            _model.to(_device)
            _model.eval()
            print("Model loaded successfully")
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
    try:
        # Check if image file exists
        import os
        if not os.path.exists(image_path):
            print(f"Image file not found: {image_path}")
            return 'moderate', 0.5, "Image file not found. Please try again."
        
        model = load_model()
        if model is None:
            print("Model could not be loaded, using fallback prediction")
            return 'moderate', 0.5, "Unable to analyze image. Please try again."
        
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
            
            # Class mapping: 0=good, 1=minor, 2=moderate, 3=severe
            class_names = ['good', 'minor', 'moderate', 'severe']
            predicted_label = class_names[predicted_class]
        
        # Apply confidence threshold for good roads
        confidence_threshold = 0.6
        if predicted_label == 'good' and confidence < confidence_threshold:
            predicted_label = 'minor'  # Default to minor if confidence is low for good roads
        
        # Generate text based on prediction
        if predicted_label == 'good':
            generated_text = generate_good_road_text()
        else:
            generated_text = generate_complaint_text(predicted_label, confidence)
        
        print(f"Prediction successful: {predicted_label} (confidence: {confidence:.2f})")
        return predicted_label, confidence, generated_text
        
    except Exception as e:
        print(f"Error processing image {image_path}: {e}")
        import traceback
        traceback.print_exc()
        return 'moderate', 0.5, "Error processing image. Please try again."

def generate_good_road_text():
    """Generate text for images of good roads"""
    messages = [
        "I'm pleased to report that this road section is in excellent condition! The surface is smooth, well-maintained, and free of any potholes or damage. This is exactly how our roads should be maintained - it's a breath of fresh air to see such quality work. Kudos to the maintenance team for keeping this area in top shape!",
        
        "What a relief! This road appears to be in pristine condition with no visible potholes or surface damage. The smooth asphalt and proper maintenance are truly commendable. It's refreshing to see a road that's been properly cared for - this is the standard we should expect everywhere.",
        
        "Excellent news! This road section is in outstanding condition. The surface is smooth, well-paved, and completely free of potholes. It's clear that proper maintenance has been carried out here, and I must say, it's a pleasure to see such quality work. This is how all our roads should look!",
        
        "I'm happy to report that this road is in perfect condition! No potholes, no damage, just smooth, well-maintained asphalt. It's wonderful to see such attention to detail in road maintenance. This level of care should be the norm across our city - well done to whoever is responsible for maintaining this area!",
        
        "This road is absolutely spotless! The surface is smooth, well-paved, and completely free of any potholes or damage. It's a joy to see such well-maintained infrastructure. This is exactly the kind of quality we should expect from our road maintenance teams - excellent work!",
        
        "What a beautiful sight! This road is in excellent condition with no visible potholes or surface damage. The smooth, well-maintained surface is a testament to proper road care. It's refreshing to see such quality maintenance work - this is how our roads should always look!",
        
        "I'm delighted to report that this road section is in outstanding condition! The surface is smooth, well-paved, and completely free of potholes. It's clear that proper maintenance has been carried out here, and I must commend the responsible authorities for their excellent work. This is the standard we should expect everywhere!"
    ]
    return random.choice(messages)

def generate_complaint_text(severity, confidence):
    """Generate complaint text based on severity and confidence"""
    
    # Add some variety with different emotional tones
    emotional_intros = {
        'minor': [
            "I've come across", "I noticed", "I've spotted", "I came across", "I discovered", "I found"
        ],
        'moderate': [
            "I'm writing to bring your urgent attention to", "I've encountered", "I'm reporting", "I've identified", "I'm concerned about", "I'm worried about"
        ],
        'severe': [
            "I'm absolutely appalled and deeply concerned about", "I'm writing with URGENT concern about", "I'm absolutely disgusted by", "I'm writing with extreme urgency about", "I'm outraged by", "I'm furious about"
        ]
    }
    
    # Emotional expressions and personalized templates for each severity level
    templates = {
        'minor': [
            "I've come across a small pothole on this road that, while not immediately threatening, is definitely worth addressing. As a concerned citizen, I can see this could develop into something more serious if left unattended. The pothole, though minor, could cause slight discomfort to drivers and potentially damage vehicle tires over time. I kindly request the authorities to take a look at this spot and fix it before it becomes a bigger problem. A little preventive maintenance now could save a lot of trouble later!",
            
            "I noticed this minor road imperfection during my daily commute, and I thought it would be helpful to bring it to your attention. While it's not causing major issues right now, I believe addressing it promptly would prevent it from worsening. As someone who uses this road regularly, I can see how these small problems can escalate if ignored. I humbly request the concerned department to please look into this matter and carry out the necessary repairs. Your prompt action would be greatly appreciated!",
            
            "I've spotted a small pothole on this road that, while not severe, is definitely something that should be fixed. As a responsible citizen, I feel it's my duty to report this issue before it becomes more problematic. The pothole, though minor, could cause inconvenience to drivers and might lead to vehicle damage if left untreated. I earnestly request the authorities to please investigate this location and take appropriate action. A stitch in time saves nine, as they say!",
            
            "I came across this minor road damage and felt compelled to report it. While it's not an emergency, I believe it's important to address these issues before they become bigger problems. As someone who cares about our community's infrastructure, I can see that this small pothole could potentially cause problems for vehicles over time. I kindly request the responsible department to please look into this matter and carry out the necessary repairs. Your attention to this issue would be much appreciated!",
            
            "I discovered this small pothole while walking my dog this morning, and I thought it would be helpful to report it. While it's not causing major problems yet, I can see it's starting to form and could become more serious if left untreated. As a local resident who cares about our neighborhood, I believe it's better to address these issues early rather than wait for them to become bigger problems. I would be grateful if the authorities could please look into this matter and carry out the necessary repairs. Thank you for your attention to this issue!",
            
            "I found this minor road imperfection while driving to work today, and I felt it was important to bring it to your attention. Although it's not an immediate safety concern, I can see how these small issues can quickly escalate if not addressed promptly. As someone who uses this road frequently, I'm concerned about the potential for this to worsen over time. I respectfully request that the responsible department please investigate this location and take appropriate action. Your prompt attention to this matter would be greatly appreciated!"
        ],
        'moderate': [
            "I'm writing to bring your urgent attention to a moderate-sized pothole on this road that poses a significant risk to public safety. As a concerned citizen, I'm genuinely worried about the potential for accidents and vehicle damage. This pothole is not just a minor inconvenience - it's a real hazard that could cause serious problems for drivers, especially during poor weather conditions. I strongly urge the authorities to prioritize this repair work immediately. The safety of our community depends on maintaining our roads properly, and this issue cannot be ignored any longer!",
            
            "I've encountered a moderate pothole on this road that has me quite concerned about public safety. This is not a minor issue that can be brushed aside - it's a legitimate road hazard that needs immediate attention. As someone who uses this road regularly, I can attest to the discomfort and potential danger this pothole poses to drivers. I'm frustrated that such issues are allowed to persist, and I demand that the responsible authorities take immediate action to repair this road. Our safety should not be compromised due to poor road maintenance!",
            
            "I'm reporting a moderate pothole on this road that I believe requires urgent attention. This is more than just a minor inconvenience - it's a safety concern that could lead to accidents or vehicle damage. As a concerned citizen, I'm disappointed that our roads are allowed to deteriorate to this extent. I strongly request the authorities to prioritize this repair work and ensure that proper road maintenance is carried out. The well-being of our community depends on having safe, well-maintained roads!",
            
            "I've identified a moderate road hazard that needs immediate attention. This pothole is causing real problems for drivers and poses a genuine safety risk. As someone who cares about our community's infrastructure, I'm concerned about the lack of proper road maintenance. I urge the responsible department to take this matter seriously and carry out the necessary repairs without delay. Our roads should be safe for everyone, and this issue cannot be overlooked any longer!",
            
            "I'm deeply concerned about a moderate pothole on this road that I encountered during my morning commute. This is not just a minor road imperfection - it's a legitimate safety hazard that could cause serious problems for drivers. As a parent who drives this road regularly, I'm worried about the potential for accidents and vehicle damage. I'm disappointed that such issues are allowed to persist, and I strongly urge the authorities to take immediate action to repair this road. The safety of our community should be the top priority!",
            
            "I'm writing with serious concern about a moderate pothole that has developed on this road. This is a real safety issue that cannot be ignored any longer. As someone who uses this road daily, I can see how this pothole is causing problems for drivers and could lead to accidents. I'm frustrated that our road maintenance seems to be inadequate, and I demand that the responsible authorities take immediate action to fix this problem. Our roads should be safe for everyone, and this issue requires urgent attention!"
        ],
        'severe': [
            "I'm absolutely appalled and deeply concerned about the severe pothole on this road! This is not just a minor inconvenience - it's a DANGEROUS hazard that poses an immediate threat to public safety. I'm genuinely angry that such a critical road condition has been allowed to exist. This pothole is a disaster waiting to happen and could cause serious accidents, vehicle damage, and even injuries. I DEMAND immediate action from the authorities - this is completely unacceptable! The safety of our community is being compromised, and I'm calling for emergency repairs RIGHT NOW. This is a matter of public safety that cannot be ignored for even one more day!",
            
            "I'm writing with URGENT concern about a severe pothole that has turned this road into a death trap! This is absolutely outrageous and completely unacceptable. As a concerned citizen, I'm furious that such a dangerous road condition has been allowed to persist. This pothole is not just a problem - it's a CRISIS that could cause serious accidents and injuries at any moment. I'm demanding immediate emergency action from the authorities. This is a matter of life and death, and I will not stand for such negligence in our road maintenance. REPAIR THIS ROAD IMMEDIATELY - our safety depends on it!",
            
            "I'm absolutely disgusted by the severe pothole on this road! This is a complete failure of our road maintenance system and a serious threat to public safety. I'm outraged that such a dangerous condition has been allowed to exist. This pothole is a disaster in the making and could cause catastrophic accidents. I'm demanding immediate action from the authorities - this is completely unacceptable! The safety of our community is being put at risk, and I'm calling for emergency repairs without any further delay. This is a matter of public safety that requires IMMEDIATE attention!",
            
            "I'm writing with extreme urgency about a severe pothole that has made this road extremely dangerous! This is absolutely unacceptable and I'm deeply concerned about the safety of everyone who uses this road. This pothole is a serious hazard that could cause major accidents and injuries. I'm demanding immediate action from the authorities - this cannot wait any longer! The safety of our community is being compromised, and I'm calling for emergency repairs RIGHT NOW. This is a matter of public safety that requires immediate attention and cannot be ignored!",
            
            "I'm FURIOUS about the severe pothole on this road! This is absolutely unacceptable and a complete disgrace to our community! As a parent who drives this road regularly, I'm terrified for the safety of my family and everyone else who uses this road. This pothole is a DEATH TRAP that could cause serious accidents at any moment. I'm absolutely outraged that such a dangerous condition has been allowed to exist. I DEMAND immediate emergency action from the authorities - this is completely unacceptable! The safety of our community is being put at risk, and I'm calling for emergency repairs RIGHT NOW!",
            
            "I'm writing with EXTREME URGENCY about a severe pothole that has made this road extremely dangerous! This is absolutely outrageous and I'm deeply concerned about the safety of everyone who uses this road. This pothole is a serious hazard that could cause major accidents and injuries. I'm demanding immediate action from the authorities - this cannot wait any longer! The safety of our community is being compromised, and I'm calling for emergency repairs RIGHT NOW. This is a matter of public safety that requires immediate attention and cannot be ignored!"
        ]
    }
    
    # Select base template
    base_text = random.choice(templates[severity])
    
    # Add confidence-based qualifier with more personality
    if confidence > 0.8:
        confidence_text = " I'm quite confident in this assessment based on the clear visual evidence."
    elif confidence > 0.6:
        confidence_text = " I'm reasonably confident in this assessment based on what I can observe."
    else:
        confidence_text = " While I'm not entirely certain, I believe this assessment is accurate based on the available information."
    
    # Add location context with more urgency based on severity
    if severity == 'severe':
        location_text = " I urge you to investigate this location IMMEDIATELY and take emergency action to repair this dangerous road condition!"
    elif severity == 'moderate':
        location_text = " I strongly request that you investigate this location promptly and take appropriate action to repair this road hazard."
    else:
        location_text = " I kindly request that you investigate this location and take appropriate action to address this road issue."
    
    return base_text + confidence_text + location_text
