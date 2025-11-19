from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from .models import Complaint, Report, UserProfile, UserNotification

User = get_user_model()

def admin_login_view(request):
    """Admin login view with special admin authentication"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user and (user.is_staff or user.is_superuser):
            login(request, user)
            messages.success(request, f'Welcome, {user.username}!')
            return redirect('admin_dashboard')
        messages.error(request, 'Invalid admin credentials or insufficient privileges.')
    
    return render(request, 'admin/login.html')

@login_required
def admin_dashboard_view(request):
    """Admin dashboard with full complaint management"""
    # Check if user is admin/staff
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('/')
    
    # Get all complaints
    complaints = Complaint.objects.all().order_by('-created_at')
    
    # Apply filters
    severity = request.GET.get('severity')
    if severity in {'minor', 'moderate', 'severe'}:
        complaints = complaints.filter(predicted_severity=severity)
    
    location = request.GET.get('location')
    if location:
        complaints = complaints.filter(location__icontains=location)
    
    public_filter = request.GET.get('public')
    if public_filter == 'true':
        complaints = complaints.filter(public=True)
    elif public_filter == 'false':
        complaints = complaints.filter(public=False)
    
    q = request.GET.get('q')
    if q:
        complaints = complaints.filter(
            Q(title__icontains=q) | 
            Q(description__icontains=q) | 
            Q(user__username__icontains=q) |
            Q(location__icontains=q)
        )
    
    # Pagination
    paginator = Paginator(complaints, 20)
    page = request.GET.get('page')
    complaints = paginator.get_page(page)
    
    # Statistics
    total_complaints = Complaint.objects.count()
    public_complaints = Complaint.objects.filter(public=True).count()
    severe_complaints = Complaint.objects.filter(predicted_severity='severe').count()
    total_users = User.objects.count()
    recently_resolved = Complaint.objects.filter(is_resolved=True).order_by('-resolved_at')[:5]
    
    context = {
        'complaints': complaints,
        'total_complaints': total_complaints,
        'public_complaints': public_complaints,
        'severe_complaints': severe_complaints,
        'total_users': total_users,
        'recently_resolved': recently_resolved,
    }
    
    return render(request, 'admin/dashboard.html', context)

@login_required
def admin_delete_complaint_view(request, pk):
    """Delete complaint (admin only)"""
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    complaint = get_object_or_404(Complaint, pk=pk)
    
    if request.method == 'POST':
        complaint.delete()
        return JsonResponse({'success': True})
    
    return JsonResponse({'error': 'Invalid method'}, status=405)

@login_required
def admin_logout_view(request):
    """Admin logout"""
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('admin_login')


@login_required
def admin_reports_view(request):
    """Admin view for managing reports"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('/')
    
    reports = Report.objects.all().order_by('-created_at')
    
    # Apply filters
    status_filter = request.GET.get('status')
    if status_filter in ['pending', 'verified', 'dismissed']:
        reports = reports.filter(status=status_filter)
    
    reason_filter = request.GET.get('reason')
    if reason_filter in ['false_complaint', 'wrong_location', 'misinformation']:
        reports = reports.filter(reason=reason_filter)
    
    q = request.GET.get('q')
    if q:
        reports = reports.filter(
            Q(complaint__title__icontains=q) |
            Q(complaint__description__icontains=q) |
            Q(reporter__username__icontains=q) |
            Q(description__icontains=q)
        )
    
    # Pagination
    paginator = Paginator(reports, 20)
    page = request.GET.get('page')
    reports = paginator.get_page(page)
    
    # Statistics
    pending_count = Report.objects.filter(status='pending').count()
    verified_count = Report.objects.filter(status='verified').count()
    dismissed_count = Report.objects.filter(status='dismissed').count()
    
    context = {
        'reports': reports,
        'pending_count': pending_count,
        'verified_count': verified_count,
        'dismissed_count': dismissed_count,
    }
    
    return render(request, 'admin/reports.html', context)


@login_required
def admin_report_detail_view(request, pk):
    """Admin view for report detail and actions"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('/')
    
    report = get_object_or_404(Report, pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'verify':
            report.status = 'verified'
            report.reviewed_by = request.user
            report.reviewed_at = timezone.now()
            report.save()
            
            # Get or create user profile
            complaint_user = report.complaint.user
            profile, _ = UserProfile.objects.get_or_create(user=complaint_user)
            
            # Increment warnings
            profile.warnings += 1
            profile.save()
            
            # Create notification for user
            UserNotification.objects.create(
                user=complaint_user,
                notification_type='warning',
                title='Account Warning',
                message=f'You have received a warning from an administrator. Your account now has {profile.warnings} warning(s). Please review our community guidelines.'
            )
            
            messages.success(request, f'Report verified. User {complaint_user.username} has been warned. (Total warnings: {profile.warnings})')
            
        elif action == 'dismiss':
            report.status = 'dismissed'
            report.reviewed_by = request.user
            report.reviewed_at = timezone.now()
            report.save()
            messages.success(request, 'Report dismissed.')
            
        elif action == 'delete_complaint':
            complaint = report.complaint
            complaint.delete()
            messages.success(request, 'Complaint deleted successfully.')
            return redirect('admin_reports')
            
        elif action == 'warn_user':
            complaint_user = report.complaint.user
            profile, _ = UserProfile.objects.get_or_create(user=complaint_user)
            profile.warnings += 1
            profile.save()
            
            # Create notification for user
            UserNotification.objects.create(
                user=complaint_user,
                notification_type='warning',
                title='Account Warning',
                message=f'You have received a warning from an administrator. Your account now has {profile.warnings} warning(s). Please review our community guidelines.'
            )
            
            messages.success(request, f'User {complaint_user.username} has been warned. (Total warnings: {profile.warnings})')
            
        elif action == 'ban_user':
            complaint_user = report.complaint.user
            profile, _ = UserProfile.objects.get_or_create(user=complaint_user)
            ban_duration = request.POST.get('ban_duration', '7')  # Default 7 days
            try:
                ban_days = int(ban_duration)
            except:
                ban_days = 7
            
            profile.is_banned = True
            profile.banned_until = timezone.now() + timedelta(days=ban_days)
            profile.ban_reason = request.POST.get('ban_reason', f'Reported complaint: {report.complaint.title}')
            profile.save()
            
            # Create notification for user
            UserNotification.objects.create(
                user=complaint_user,
                notification_type='ban',
                title='Account Banned',
                message=f'Your account has been temporarily banned for {ban_days} days. Reason: {profile.ban_reason}'
            )
            
            messages.success(request, f'User {complaint_user.username} has been banned for {ban_days} days.')
            
        elif action == 'permanent_ban':
            complaint_user = report.complaint.user
            profile, _ = UserProfile.objects.get_or_create(user=complaint_user)
            profile.is_banned = True
            profile.banned_until = None  # Permanent ban
            profile.ban_reason = request.POST.get('ban_reason', f'Reported complaint: {report.complaint.title}')
            profile.save()
            
            # Create notification for user
            UserNotification.objects.create(
                user=complaint_user,
                notification_type='ban',
                title='Account Permanently Banned',
                message=f'Your account has been permanently banned. Reason: {profile.ban_reason}'
            )
            
            messages.success(request, f'User {complaint_user.username} has been permanently banned.')
        
        return redirect('admin_report_detail', pk=pk)
    
    # Get user profile info
    complaint_user = report.complaint.user
    profile, _ = UserProfile.objects.get_or_create(user=complaint_user)
    
    context = {
        'report': report,
        'complaint': report.complaint,
        'user_profile': profile,
    }
    
    return render(request, 'admin/report_detail.html', context)


@login_required
def admin_create_government_user_view(request):
    """Admin view to create government users"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('/')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if not username or not email or not password:
            messages.error(request, 'Please fill in all fields.')
        else:
            try:
                # Create user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password
                )
                
                # Create profile and mark as government user
                profile, _ = UserProfile.objects.get_or_create(user=user)
                profile.is_government_user = True
                profile.save()
                
                messages.success(request, f'Government user {username} created successfully!')
                return redirect('admin_government_users')
            except Exception as e:
                messages.error(request, f'Error creating user: {str(e)}')
    
    return render(request, 'admin/create_government_user.html')


@login_required
def admin_government_users_view(request):
    """Admin view to list government users"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('/')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'promote_existing':
            username = request.POST.get('username')
            user = User.objects.filter(username__iexact=username).first()
            if not user:
                messages.error(request, f'User "{username}" was not found.')
            else:
                profile, _ = UserProfile.objects.get_or_create(user=user)
                profile.is_government_user = True
                profile.save()
                messages.success(request, f'User {user.username} is now a government operator.')
        elif action == 'demote':
            user_id = request.POST.get('user_id')
            profile = UserProfile.objects.filter(user_id=user_id, is_government_user=True).first()
            if profile:
                profile.is_government_user = False
                profile.save()
                messages.success(request, f'User {profile.user.username} is no longer a government operator.')
            else:
                messages.error(request, 'Unable to find that government user.')
        return redirect('admin_government_users')
    
    government_users = UserProfile.objects.filter(is_government_user=True).select_related('user')
    
    context = {
        'government_users': government_users,
    }
    
    return render(request, 'admin/government_users.html', context)
