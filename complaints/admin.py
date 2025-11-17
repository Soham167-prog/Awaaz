from django.contrib import admin
from .models import Complaint, Comment, AadhaarOTP, Report, UserProfile, UserNotification, Announcement

# Register your models here.
class CommentInline(admin.TabularInline):
    model = Comment
    extra = 1
    readonly_fields = ('created_at',)
    fields = ('user', 'text', 'created_at')
    show_change_link = True

class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_at', 'predicted_severity', 'confidence')
    list_filter = ('predicted_severity', 'created_at')
    search_fields = ('title', 'description', 'user__username')
    readonly_fields = ('created_at',)
    inlines = [CommentInline]
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:  # Only set user if this is a new object
            obj.user = request.user
        super().save_model(request, obj, form, change)

class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'short_text', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('text', 'user__username')
    readonly_fields = ('created_at',)
    
    def short_text(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    short_text.short_description = 'Comment'

class AadhaarOTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'expires_at', 'verified')
    list_filter = ('verified', 'created_at')
    search_fields = ('user__username',)
    readonly_fields = ('created_at', 'expires_at', 'attempts')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

class ReportAdmin(admin.ModelAdmin):
    list_display = ('complaint', 'reporter', 'reason', 'status', 'created_at', 'reviewed_by')
    list_filter = ('status', 'reason', 'created_at')
    search_fields = ('complaint__title', 'reporter__username', 'description')
    readonly_fields = ('created_at', 'reviewed_at')
    actions = ['mark_verified', 'mark_dismissed']
    
    def mark_verified(self, request, queryset):
        queryset.update(status='verified', reviewed_by=request.user)
    mark_verified.short_description = "Mark selected reports as verified"
    
    def mark_dismissed(self, request, queryset):
        queryset.update(status='dismissed', reviewed_by=request.user)
    mark_dismissed.short_description = "Mark selected reports as dismissed"

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'warnings', 'is_banned', 'is_government_user', 'banned_until', 'created_at')
    list_filter = ('is_banned', 'is_government_user', 'warnings', 'created_at')
    search_fields = ('user__username', 'ban_reason')
    readonly_fields = ('created_at',)

class UserNotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'title', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'title', 'message')
    readonly_fields = ('created_at',)

admin.site.register(Complaint, ComplaintAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(AadhaarOTP, AadhaarOTPAdmin)
admin.site.register(Report, ReportAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(UserNotification, UserNotificationAdmin)
@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'audience', 'is_published', 'published_at', 'created_by')
    list_filter = ('audience', 'is_published', 'published_at')
    search_fields = ('title', 'body')
    readonly_fields = ('created_at', 'published_at')
