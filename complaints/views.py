from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
import json
from .forms import ComplaintForm, CommentForm, SeverityCorrectionForm, EditComplaintForm
from .models import Complaint
from .services import predict_and_generate_text

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

@login_required
def upload_view(request):
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
    return render(request, 'complaints/detail.html', {'obj': obj, 'comment_form': comment_form, 'corr_form': corr_form})

@login_required
def upvote_view(request, pk: int):
    obj = get_object_or_404(Complaint, pk=pk)
    if request.user in obj.upvotes.all():
        obj.upvotes.remove(request.user)
    else:
        obj.upvotes.add(request.user)
    return redirect('complaint_detail', pk=pk)

@login_required
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
def correct_severity_view(request, pk: int):
    obj = get_object_or_404(Complaint, pk=pk)
    if request.method == 'POST':
        form = SeverityCorrectionForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Thanks! Your correction helps improve the model.')
    return redirect('complaint_detail', pk=pk)

@login_required
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
