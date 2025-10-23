from django import forms
from .models import Complaint, Comment, SEVERITY_CHOICES

class ComplaintForm(forms.ModelForm):
	class Meta:
		model = Complaint
		fields = ['image', 'public', 'location']
		widgets = {
			'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter location (e.g., Main Street, Downtown)'})
		}

class EditComplaintForm(forms.ModelForm):
	class Meta:
		model = Complaint
		fields = ['title', 'description', 'predicted_severity', 'generated_text']
		widgets = {
			'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter a title for your complaint'}),
			'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Add any additional details about the road condition'}),
			'predicted_severity': forms.Select(attrs={'class': 'form-control'}),
			'generated_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'AI-generated complaint text (you can edit this)'})
		}

class CommentForm(forms.ModelForm):
	class Meta:
		model = Comment
		fields = ['text']
		widgets = {
			'text': forms.Textarea(attrs={'rows': 2})
		}

class SeverityCorrectionForm(forms.ModelForm):
	true_severity = forms.ChoiceField(choices=SEVERITY_CHOICES, required=True)
	class Meta:
		model = Complaint
		fields = ['true_severity']

class AadhaarStartForm(forms.Form):
	aadhaar_number = forms.CharField(max_length=12, min_length=12)

class AadhaarOTPForm(forms.Form):
	otp = forms.CharField(max_length=6, min_length=6)
