from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

SEVERITY_CHOICES = [
	('minor', 'Minor'),
	('moderate', 'Moderate'),
	('severe', 'Severe'),
]

STATUS_CHOICES = [
	('pending', 'Pending Review'),
	('in_progress', 'Repair In Progress'),
	('resolved', 'Grievance Resolved'),
]

class Complaint(models.Model):
	created_at = models.DateTimeField(auto_now_add=True)
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaints', null=True, blank=True)
	title = models.CharField(max_length=120, blank=True)
	description = models.TextField(blank=True)
	image = models.ImageField(upload_to='complaints/')
	predicted_severity = models.CharField(max_length=16, choices=SEVERITY_CHOICES)
	true_severity = models.CharField(max_length=16, choices=SEVERITY_CHOICES, blank=True, default='')
	confidence = models.FloatField(default=0.0)
	generated_text = models.TextField(blank=True)
	mongo_file_id = models.CharField(max_length=64, blank=True, default='')
	public = models.BooleanField(default=True)
	upvotes = models.ManyToManyField(User, related_name='upvoted_complaints', blank=True)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
	assigned_department = models.CharField(max_length=100, default='Municipal PWD Dept')

	def __str__(self) -> str:
		return f"{self.pk} - {self.predicted_severity} ({self.confidence:.2f})"

	@property
	def upvote_count(self) -> int:
		return self.upvotes.count()

class Comment(models.Model):
	complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='comments')
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
	text = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)
	is_govt_response = models.BooleanField(default=False)
	is_admin_response = models.BooleanField(default=False)

	def __str__(self) -> str:
		return f"Comment {self.pk} on {self.complaint_id} by {self.user_id}"

class AadhaarOTP(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='aadhaar_otps')
	aadhaar_hash = models.CharField(max_length=128)
	otp_hash = models.CharField(max_length=128)
	created_at = models.DateTimeField(auto_now_add=True)
	expires_at = models.DateTimeField()
	attempts = models.IntegerField(default=0)
	verified = models.BooleanField(default=False)

	def is_expired(self) -> bool:
		return timezone.now() >= self.expires_at
