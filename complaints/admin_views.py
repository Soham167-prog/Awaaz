from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.db.models import Q, Count
from .models import Complaint

def admin_login_view(request):
    """Admin login view with special admin authentication"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Check if user exists and is staff/admin
        try:
            user = User.objects.get(username=username)
            if user.check_password(password) and (user.is_staff or user.is_superuser):
                from django.contrib.auth import login
                login(request, user)
                messages.success(request, f'Welcome, {user.username}!')
                return redirect('admin_dashboard')
            else:
                messages.error(request, 'Invalid admin credentials.')
        except User.DoesNotExist:
            messages.error(request, 'Invalid admin credentials.')
    
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
    
    context = {
        'complaints': complaints,
        'total_complaints': total_complaints,
        'public_complaints': public_complaints,
        'severe_complaints': severe_complaints,
        'total_users': total_users,
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
    from django.contrib.auth import logout
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('admin_login')
