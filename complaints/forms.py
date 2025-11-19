from django import forms
from .models import Complaint, Comment, Announcement

# Import SEVERITY_CHOICES from Complaint model
SEVERITY_CHOICES = Complaint.SEVERITY_CHOICES

class ComplaintForm(forms.ModelForm):
	class Meta:
		model = Complaint
		fields = ['image', 'public', 'location']
		widgets = {
			'location': forms.TextInput(attrs={
				'class': 'form-control', 
				'placeholder': 'Enter location (e.g., Main Street, Downtown)',
				'style': 'background-color: #000000 !important; color: #f5f5f7 !important; border: 1px solid #2a2a36 !important;'
			})
		}

class EditComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['title', 'description', 'predicted_severity', 'generated_text', 'public', 'location']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter a title for your complaint',
                'style': 'background-color: #000000 !important; color: #f5f5f7 !important; border: 1px solid #2a2a36 !important;'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Add any additional details about the road condition',
                'style': 'background-color: #000000 !important; color: #f5f5f7 !important; border: 1px solid #2a2a36 !important;'
            }),
            'predicted_severity': forms.Select(attrs={
                'class': 'form-control',
                'style': 'background-color: #000000 !important; color: #f5f5f7 !important; border: 1px solid #2a2a36 !important;'
            }, choices=SEVERITY_CHOICES),
            'generated_text': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4, 
                'placeholder': 'AI-generated complaint text (you can edit this)',
                'style': 'background-color: #000000 !important; color: #f5f5f7 !important; border: 1px solid #2a2a36 !important;'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter location (e.g., Main Street, Downtown)',
                'style': 'background-color: #000000 !important; color: #f5f5f7 !important; border: 1px solid #2a2a36 !important;'
            })
        }

class CommentForm(forms.ModelForm):
	class Meta:
		model = Comment
		fields = ['text']
		widgets = {
			'text': forms.Textarea(attrs={
				'class': 'form-control', 
				'rows': 2,
				'style': 'background-color: #000000 !important; color: #f5f5f7 !important; border: 1px solid #2a2a36 !important;'
			})
		}

class SeverityCorrectionForm(forms.ModelForm):
    true_severity = forms.ChoiceField(
        choices=SEVERITY_CHOICES, 
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'style': 'background-color: #000000 !important; color: #f5f5f7 !important; border: 1px solid #2a2a36 !important;'
        })
    )
    
    class Meta:
        model = Complaint
        fields = ['true_severity']
#Aadhaar Authentication Forms(Optional after Aadhaar authentication)
class AadhaarStartForm(forms.Form):
	aadhaar_number = forms.CharField(max_length=12, min_length=12)

class AadhaarOTPForm(forms.Form):
	otp = forms.CharField(max_length=6, min_length=6)


class GovernmentCommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4, 
                'placeholder': 'Add an official update...',
                'style': 'background-color: #000000 !important; color: #f5f5f7 !important; border: 1px solid #2a2a36 !important;'
            }),
        }


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'body', 'audience', 'is_published']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Announcement title',
                'style': 'background-color: #000000 !important; color: #f5f5f7 !important; border: 1px solid #2a2a36 !important;'
            }),
            'body': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 6, 
                'placeholder': 'Announcement details',
                'style': 'background-color: #000000 !important; color: #f5f5f7 !important; border: 1px solid #2a2a36 !important;'
            }),
            'audience': forms.Select(attrs={
                'class': 'form-control',
                'style': 'background-color: #000000 !important; color: #f5f5f7 !important; border: 1px solid #2a2a36 !important;'
            }),
        }


class ReportForm(forms.ModelForm):
    class Meta:
        from .models import Report
        model = Report
        fields = ['reason', 'description']
        widgets = {
            'reason': forms.Select(attrs={
                'class': 'form-control',
                'style': 'background-color: #000000 !important; color: #f5f5f7 !important; border: 1px solid #2a2a36 !important;'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4, 
                'placeholder': 'Please provide additional details about why you are reporting this complaint (optional)',
                'style': 'background-color: #000000 !important; color: #f5f5f7 !important; border: 1px solid #2a2a36 !important;'
            })
        }
