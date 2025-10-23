import os
import uuid
from typing import Any, Dict

from django.core.files.storage import default_storage

from .services import predict_and_generate_text


def process_complaint_image(image: Any) -> Dict[str, str]:
    """
    Process an uploaded image and return a draft complaint text and severity.

    Accepts either:
    - a file-like object (e.g., InMemoryUploadedFile) OR
    - a string file path to an existing image on disk

    Returns a dict: { 'draft': str, 'severity': str }
    """
    temp_path = None
    try:
        # If we received a path string, use it directly
        if isinstance(image, str) and os.path.exists(image):
            temp_path = image
        else:
            # Save file-like to a temporary storage path
            # Try to infer extension; default to .jpg
            ext = getattr(image, 'name', '')
            ext = os.path.splitext(ext)[1] if ext else '.jpg'
            name = f"temp/{uuid.uuid4().hex}{ext or '.jpg'}"
            temp_name = default_storage.save(name, image)
            temp_path = default_storage.path(temp_name)

        # Use existing model service to get severity and text
        predicted_label, confidence, generated_text = predict_and_generate_text(temp_path)

        # Map to the expected keys
        return {
            'draft': generated_text or 'Generated complaint text',
            'severity': str(predicted_label) if predicted_label else 'moderate',
        }
    except Exception:
        # Safe fallback
        return {
            'draft': 'Generated complaint text',
            'severity': 'moderate',
        }
    finally:
        # Clean up temporary file if we created one via default_storage
        try:
            if temp_path and not (isinstance(image, str) and image == temp_path):
                # Convert back to storage name relative to storage root
                # default_storage.delete expects the name used in save, but we have full path.
                # If delete by path is unsupported, attempt os.remove as a fallback.
                rel_name = None
                if hasattr(default_storage, 'path'):
                    # Try to compute relative name by stripping base path
                    base_dir = os.path.dirname(default_storage.path('x'))[:-1]
                    if temp_path.startswith(base_dir):
                        rel_name = temp_path[len(base_dir)+1:]
                if rel_name:
                    default_storage.delete(rel_name)
                else:
                    os.remove(temp_path)
        except Exception:
            pass


