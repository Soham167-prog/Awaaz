from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
import json
from .forms import ComplaintForm, CommentForm, SeverityCorrectionForm, EditComplaintForm, ReportForm
from .models import Complaint, Report, UserProfile, UserNotification, Comment, Announcement
from .decorators import citizen_required
from .services import predict_and_generate_text
from django.utils import timezone

# Optional: Mongo GridFS
try:
    from pymongo import MongoClient
    from gridfs import GridFS
    MONGO_AVAILABLE = True
except Exception:
    MONGO_AVAILABLE = False


def _save_to_mongo(path: str) -> str:
    if not MONGO_AVAILABLE:
        return ''
    uri = getattr(settings, 'MONGO_URI', '')
    if not uri:
        return ''
    client = MongoClient(uri)
    db = client.get_database()
    fs = GridFS(db)
    with open(path, 'rb') as f:
        file_id = fs.put(f, filename=path.split('/')[-1])
    return str(file_id)


def feed_view(request):
    qs = Complaint.objects.filter(public=True)
    severity = request.GET.get('severity')
    if severity in {'minor', 'moderate', 'severe'}:
        qs = qs.filter(predicted_severity=severity)
    
    location = request.GET.get('location')
    if location:
        qs = qs.filter(location__icontains=location)
    
    q = request.GET.get('q')
    if q:
        qs = qs.filter(title__icontains=q) | qs.filter(description__icontains=q) | qs.filter(location__icontains=q)
    
    sort = request.GET.get('sort')
    if sort == 'top':
        qs = sorted(qs, key=lambda c: c.upvote_count, reverse=True)
    else:
        qs = qs.order_by('-created_at')
    
    p = Paginator(qs, 9)
    page = request.GET.get('page')
    items = p.get_page(page)
    
    # Get unique locations for filter dropdown
    locations = Complaint.objects.filter(public=True).exclude(location='').values_list('location', flat=True).distinct().order_by('location')
    
    # Check if user is admin
    is_admin = request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)
    
    return render(request, 'complaints/feed.html', { 
        'items': items,
        'is_admin': is_admin,
        'locations': locations
    })

def _check_user_banned(user):
    """Check if user is banned and return True if banned"""
    if not user.is_authenticated:
        return False
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile.is_currently_banned()


@login_required
@citizen_required
def upload_view(request):
    # Check if user is banned
    if _check_user_banned(request.user):
        messages.error(request, 'Your account has been banned. You cannot create complaints.')
        return redirect('feed')
    
    if request.method == 'POST':
        # Check if this is an AJAX request for analysis
        if request.headers.get('Content-Type') == 'application/json' or 'application/json' in request.headers.get('Content-Type', ''):
            try:
                data = json.loads(request.body)
                action = data.get('action')
            except:
                action = None
        else:
            action = request.POST.get('action')
        
        # Handle analysis request (AJAX)
        if action == 'analyze' or (not action and request.FILES.get('image')):
            uploaded = request.FILES.get('image')
            if not uploaded:
                return JsonResponse({'success': False, 'error': 'Please choose an image to upload.'})
            
            try:
                # Save file temporarily without creating database record
                import os
                import tempfile
                from django.core.files.storage import default_storage
                
                # Create a temporary file path
                temp_path = default_storage.save(f'temp/{uploaded.name}', uploaded)
                full_path = default_storage.path(temp_path)
                
                # Get prediction
                pred, conf, text = predict_and_generate_text(full_path)
                
                # Clean up temporary file
                default_storage.delete(temp_path)
                
                # Return analysis results
                return JsonResponse({
                    'success': True,
                    'severity': pred,
                    'confidence': conf,
                    'generated_text': text,
                    'image_url': None  # No image URL for analysis
                })
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Error processing image: {str(e)}'})
        
        # Handle posting to feed
        elif action == 'post':
            uploaded = request.FILES.get('image')
            if not uploaded:
                return JsonResponse({'success': False, 'error': 'Please choose an image to upload.'})
            
            public_raw = str(request.POST.get('public', '')).lower()
            public_flag = public_raw in ('true', 'on', '1', 'yes')
            complaint = Complaint(user=request.user, public=public_flag)
            complaint.image = uploaded
            complaint.title = request.POST.get('title', '')
            complaint.description = request.POST.get('description', '')
            complaint.location = request.POST.get('location', '')
            complaint.predicted_severity = request.POST.get('predicted_severity', 'moderate')
            complaint.confidence = float(request.POST.get('confidence', 0.5))
            complaint.generated_text = request.POST.get('generated_text', '')
            complaint.save()
            complaint.mongo_file_id = _save_to_mongo(complaint.image.path)
            complaint.save()
            return JsonResponse({'success': True, 'redirect_url': reverse('feed')})
        
        # Handle regular form submission (fallback)
        else:
            uploaded = request.FILES.get('image')
            if not uploaded:
                return render(request, 'complaints/upload.html', {'form': ComplaintForm()})
            public_raw = str(request.POST.get('public', '')).lower()
            public_flag = public_raw in ('true', 'on', '1', 'yes')
            complaint = Complaint(user=request.user, public=public_flag)
            complaint.image = uploaded
            complaint.save()  # saves file to disk
            pred, conf, text = predict_and_generate_text(complaint.image.path)
            complaint.predicted_severity = pred
            complaint.confidence = conf
            complaint.generated_text = text
            complaint.mongo_file_id = _save_to_mongo(complaint.image.path)
            complaint.save()
            return redirect('complaint_detail', pk=complaint.pk)
    
    # GET
    return render(request, 'complaints/upload.html', {'form': ComplaintForm()})


def detail_view(request, pk: int):
    obj = get_object_or_404(Complaint, pk=pk)
    comment_form = CommentForm()
    corr_form = SeverityCorrectionForm(instance=obj)
    is_gov_user = _is_government_user(request.user) if request.user.is_authenticated else False
    official_comments = obj.comments.filter(is_official_comment=True).order_by('-created_at')
    citizen_comments = obj.comments.filter(is_official_comment=False).order_by('-created_at')

    return render(request, 'complaints/detail.html', {
        'obj': obj,
        'comment_form': comment_form,
        'corr_form': corr_form,
        'is_gov_user': is_gov_user,
        'official_comments': official_comments,
        'citizen_comments': citizen_comments,
    })

@login_required
@citizen_required
def upvote_view(request, pk: int):
    obj = get_object_or_404(Complaint, pk=pk)
    if request.user in obj.upvotes.all():
        obj.upvotes.remove(request.user)
    else:
        obj.upvotes.add(request.user)
    return redirect('complaint_detail', pk=pk)

@login_required
@citizen_required
def comment_create_view(request, pk: int):
    obj = get_object_or_404(Complaint, pk=pk)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            c = form.save(commit=False)
            c.user = request.user
            c.complaint = obj
            c.save()
    return redirect('complaint_detail', pk=pk)

@login_required
@citizen_required
def correct_severity_view(request, pk: int):
    obj = get_object_or_404(Complaint, pk=pk)
    if request.method == 'POST':
        form = SeverityCorrectionForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Thanks! Your correction helps improve the model.')
    return redirect('complaint_detail', pk=pk)

@login_required
@citizen_required
def edit_complaint_view(request, pk: int):
    obj = get_object_or_404(Complaint, pk=pk)
    
    # Check if user owns the complaint or is staff
    if obj.user != request.user and not request.user.is_staff:
        messages.error(request, 'You can only edit your own complaints.')
        return redirect('complaint_detail', pk=pk)
    
    if request.method == 'POST':
        form = EditComplaintForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Complaint updated successfully!')
            return redirect('complaint_detail', pk=pk)
    else:
        form = EditComplaintForm(instance=obj)
    
    return render(request, 'complaints/edit.html', {'form': form, 'complaint': obj})

@login_required
def delete_complaint_view(request, pk: int):
    """Delete complaint (admin only)"""
    obj = get_object_or_404(Complaint, pk=pk)
    
    # Check if user is admin or owns the complaint
    if not (request.user.is_staff or request.user.is_superuser) and obj.user != request.user:
        messages.error(request, 'You can only delete your own complaints or need admin privileges.')
        return redirect('complaint_detail', pk=pk)
    
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Complaint deleted successfully!')
        return redirect('/')
    
    return render(request, 'complaints/delete_confirm.html', {'complaint': obj})


@login_required
@citizen_required
def report_complaint_view(request, pk: int):
    """Report a complaint"""
    complaint = get_object_or_404(Complaint, pk=pk)
    
    # Check if user is banned
    if _check_user_banned(request.user):
        messages.error(request, 'Your account has been banned. You cannot report complaints.')
        return redirect('complaint_detail', pk=pk)
    
    # Check if user already reported this complaint
    existing_report = Report.objects.filter(complaint=complaint, reporter=request.user).first()
    if existing_report:
        messages.info(request, 'You have already reported this complaint.')
        return redirect('complaint_detail', pk=pk)
    
    # Can't report your own complaint
    if complaint.user == request.user:
        messages.error(request, 'You cannot report your own complaint.')
        return redirect('complaint_detail', pk=pk)
    
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.complaint = complaint
            report.reporter = request.user
            report.save()
            messages.success(request, 'Thank you for reporting. We will review this complaint.')
            return redirect('complaint_detail', pk=pk)
    else:
        form = ReportForm()
    
    return render(request, 'complaints/report.html', {'form': form, 'complaint': complaint})


def _is_government_user(user):
    """Check if user is a government user"""
    if not user.is_authenticated:
        return False
    try:
        profile = user.profile
        return profile.is_government_user
    except UserProfile.DoesNotExist:
        return False


@login_required
def mark_complaint_resolved_view(request, pk: int):
    """Government user view to mark complaint as resolved"""
    complaint = get_object_or_404(Complaint, pk=pk)
    
    # Check if user is government user
    if not _is_government_user(request.user):
        messages.error(request, 'Only government users can mark complaints as resolved.')
        return redirect('complaint_detail', pk=pk)
    
    if request.method == 'POST':
        resolution_comment = request.POST.get('resolution_comment', '')
        
        # Mark complaint as resolved
        complaint.is_resolved = True
        complaint.resolved_at = timezone.now()
        complaint.resolved_by = request.user
        complaint.save()
        
        # Create resolution comment if provided
        if resolution_comment:
            Comment.objects.create(
                complaint=complaint,
                user=request.user,
                text=resolution_comment,
                is_resolution_comment=True,
                is_official_comment=True
            )
        
        # Create notification for complaint owner
        UserNotification.objects.create(
            user=complaint.user,
            notification_type='complaint_resolved',
            title='Complaint Resolved',
            message=f'Your complaint "{complaint.title}" has been marked as resolved by a government official.'
        )
        
        messages.success(request, 'Complaint marked as resolved successfully!')
        return redirect('complaint_detail', pk=pk)
    
    return render(request, 'complaints/mark_resolved.html', {'complaint': complaint})


@login_required
def notifications_view(request):
    """View user notifications"""
    notifications = request.user.notifications.all()[:20]  # Last 20 notifications
    unread_count = request.user.notifications.filter(is_read=False).count()
    
    # Mark all as read when viewing
    request.user.notifications.filter(is_read=False).update(is_read=True)
    
    return render(request, 'complaints/notifications.html', {
        'notifications': notifications,
        'unread_count': unread_count
    })


def announcements_view(request):
    announcements = Announcement.objects.filter(
        is_published=True,
        audience__in=['all', 'citizen']
    ).order_by('-published_at')
    return render(request, 'announcements/list.html', {
        'announcements': announcements,
    })
