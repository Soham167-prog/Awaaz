import streamlit as st
import torch
import cv2
import numpy as np
import uuid
from datetime import datetime
from src.models.model import PotholeSeverityModel
from src.data.dataset import CLASS_NAMES, _resize_and_pad, _to_tensor
from .admin import report_complaint, show_admin_panel
from .db import db
from .models import ReportType, User, UserStatus

@st.cache_resource
def load_model(checkpoint_path: str):
	device = torch.device("mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu"))
	model = PotholeSeverityModel.create(num_classes=len(CLASS_NAMES), pretrained=False)
	ckpt = torch.load(checkpoint_path, map_location=device)
	model.load_state_dict(ckpt["model_state"]) 
	model.to(device)
	model.eval()
	return model, device

# Initialize session state for user
if 'user_id' not in st.session_state:
    # In a real app, you would have proper user authentication
    st.session_state.user_id = f"user_{str(uuid.uuid4())[:8]}"
    # Create user in database if not exists
    user = db.get_user(st.session_state.user_id)
    if not user:
        user = User(
            id=st.session_state.user_id,
            email=f"{st.session_state.user_id}@example.com",
            created_at=datetime.now(),
            status=UserStatus.ACTIVE,
            warnings=0
        )
        # In a real app, you would save the user to the database here

st.set_page_config(page_title="Pothole Severity Classifier", page_icon="🕳️", layout="centered")

# Navigation
page = st.sidebar.radio("Navigation", ["Home", "Report Issue", "Admin"])

if page == "Admin":
    show_admin_panel()
    st.stop()

st.title("Pothole Severity Classifier")

checkpoint_path = st.text_input("Checkpoint path", value="checkpoints/best.pt")

uploaded = st.file_uploader("Upload a road image", type=["jpg","jpeg","png"])

if page == "Home":
    if uploaded and checkpoint_path:
        # Generate a unique ID for this complaint
        complaint_id = f"comp_{int(datetime.now().timestamp())}"
        
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
                confidence = float(probs[pred_idx])
                
                st.subheader(f"Prediction: {pred_label} (Confidence: {confidence:.2f})")
                
                # Display probabilities
                st.write("Class Probabilities:")
                for i, class_name in enumerate(CLASS_NAMES):
                    st.write(f"- {class_name}: {probs[i]:.4f}")
                
                # Store prediction in session state for reporting
                st.session_state.current_prediction = {
                    'id': complaint_id,
                    'class': pred_label,
                    'confidence': confidence,
                    'image': rgb
                }
                
                # Show report button
                if st.button("Report Incorrect Classification"):
                    st.session_state.show_report_form = True
                
                # Report form
                if st.session_state.get('show_report_form', False):
                    with st.form("report_form"):
                        st.write("### Report Incorrect Classification")
                        report_type = st.selectbox(
                            "What's wrong with this classification?",
                            [rt.value for rt in ReportType],
                            format_func=lambda x: x.replace('_', ' ').title()
                        )
                        description = st.text_area("Please provide more details")
                        
                        submitted = st.form_submit_button("Submit Report")
                        if submitted:
                            if not description.strip():
                                st.error("Please provide a description")
                            else:
                                report_complaint(
                                    complaint_id=complaint_id,
                                    report_type=report_type,
                                    description=description,
                                    user_id=st.session_state.user_id
                                )
                                st.success("Thank you for your report. Our team will review it shortly.")
                                st.session_state.show_report_form = False
                                st.experimental_rerun()

elif page == "Report Issue":
    st.header("Report an Issue")
    st.write("If you have any issues or feedback, please let us know.")
    
    with st.form("issue_form"):
        issue_type = st.selectbox(
            "Type of Issue",
            ["Bug Report", "Feature Request", "General Feedback"]
        )
        description = st.text_area("Please describe the issue in detail")
        email = st.text_input("Your Email (optional)")
        
        submitted = st.form_submit_button("Submit")
        if submitted:
            if not description.strip():
                st.error("Please provide a description")
            else:
                # In a real app, you would save this to a database
                st.success("Thank you for your feedback! We'll look into it.")
                
                # Log the issue (in a real app, save to database)
                print(f"New {issue_type} from {email or 'anonymous'}: {description}")
                st.balloons()
