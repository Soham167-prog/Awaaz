from django import forms
from .models import Complaint, Comment, SEVERITY_CHOICES

class ComplaintForm(forms.ModelForm):
	class Meta:
		model = Complaint
		fields = ['image', 'public']

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
