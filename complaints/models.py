from django.db import models
from django.contrib.auth.models import User

class Complaint(models.Model):
    SEVERITY_CHOICES = [
        ('minor', 'Minor'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe'),
        ('critical', 'Critical'),
    ]
    
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaints')
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='complaints/')
    predicted_severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    true_severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, blank=True, null=True)
    confidence = models.FloatField()
    generated_text = models.TextField(blank=True)
    mongo_file_id = models.CharField(max_length=100, blank=True)
    public = models.BooleanField(default=True)
    location = models.CharField(max_length=200, blank=True)
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_complaints')

    def __str__(self):
        return f"{self.title} - {self.get_true_severity_display() if self.true_severity else self.get_predicted_severity_display()}"

class Comment(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolution_comment = models.BooleanField(default=False)  # Special comment for resolution
    is_official_comment = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.text[:50]}..."

class AadhaarOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='aadhaar_otps')
    aadhaar_hash = models.CharField(max_length=128)
    otp_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    attempts = models.IntegerField(default=0)
    verified = models.BooleanField(default=False)

    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at


class UserProfile(models.Model):
    """Extended user profile for warnings and bans"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    warnings = models.IntegerField(default=0)
    is_banned = models.BooleanField(default=False)
    banned_until = models.DateTimeField(null=True, blank=True)
    ban_reason = models.TextField(blank=True)
    is_government_user = models.BooleanField(default=False)  # Government user can mark complaints as resolved
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - Warnings: {self.warnings}, Banned: {self.is_banned}, Gov: {self.is_government_user}"
    
    def is_currently_banned(self):
        from django.utils import timezone
        if not self.is_banned:
            return False
        if self.banned_until and timezone.now() > self.banned_until:
            self.is_banned = False
            self.save()
            return False
        return True


class UserNotification(models.Model):
    """Notifications for users (warnings, bans, etc.)"""
    NOTIFICATION_TYPES = [
        ('warning', 'Warning'),
        ('ban', 'Ban'),
        ('ban_lifted', 'Ban Lifted'),
        ('complaint_resolved', 'Complaint Resolved'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_notification_type_display()} - {self.title}"


class Report(models.Model):
    REASON_CHOICES = [
        ('false_complaint', 'False Complaint'),
        ('wrong_location', 'Wrong Location'),
        ('misinformation', 'Misinformation'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('dismissed', 'Dismissed'),
    ]
    
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='reports')
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made')
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    description = models.TextField(blank=True, help_text="Additional details about the report")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports_reviewed')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = [['complaint', 'reporter']]  # One report per user per complaint
    
    def __str__(self):
        return f"Report on {self.complaint.title} - {self.get_reason_display()} ({self.get_status_display()})"


class Announcement(models.Model):
    AUDIENCE_CHOICES = [
        ('citizen', 'Citizens'),
        ('government', 'Government Officials'),
        ('all', 'Everyone'),
    ]

    title = models.CharField(max_length=200)
    body = models.TextField()
    audience = models.CharField(max_length=20, choices=AUDIENCE_CHOICES, default='all')
    is_published = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='announcements')
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-published_at']

    def __str__(self):
        return f"{self.title} ({self.get_audience_display()})"
