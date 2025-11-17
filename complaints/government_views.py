from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .decorators import government_required
from .forms import GovernmentCommentForm, AnnouncementForm
from .models import Announcement, Comment, Complaint


@login_required
@government_required
def dashboard_view(request):
    """Government dashboard showing pending complaints and announcements."""
    pending_complaints = Complaint.objects.filter(is_resolved=False).order_by('-created_at')[:10]
    recently_resolved = Complaint.objects.filter(is_resolved=True).order_by('-resolved_at')[:5]
    total_pending = Complaint.objects.filter(is_resolved=False).count()
    total_resolved = Complaint.objects.filter(is_resolved=True).count()

    recent_announcements = Announcement.objects.filter(
        audience__in=['government', 'all'],
        is_published=True
    ).order_by('-published_at')[:5]

    context = {
        'pending_complaints': pending_complaints,
        'recently_resolved': recently_resolved,
        'total_pending': total_pending,
        'total_resolved': total_resolved,
        'recent_announcements': recent_announcements,
        'now': timezone.now(),
    }
    return render(request, 'government/dashboard.html', context)


@login_required
@government_required
def complaint_detail_view(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk)
    comment_form = GovernmentCommentForm()

    if request.method == 'POST' and request.POST.get('action') == 'comment':
        comment_form = GovernmentCommentForm(request.POST)
        if comment_form.is_valid():
            comment: Comment = comment_form.save(commit=False)
            comment.complaint = complaint
            comment.user = request.user
            comment.is_official_comment = True
            comment.save()
            messages.success(request, 'Official comment added successfully.')
            return redirect('government_complaint_detail', pk=pk)
        messages.error(request, 'Please correct the errors in your comment.')

    official_comments = complaint.comments.filter(is_official_comment=True).order_by('-created_at')
    citizen_comments = complaint.comments.filter(is_official_comment=False).order_by('-created_at')

    context = {
        'complaint': complaint,
        'comment_form': comment_form,
        'official_comments': official_comments,
        'citizen_comments': citizen_comments,
    }
    return render(request, 'government/complaint_detail.html', context)


@login_required
@government_required
def announcements_view(request):
    announcements = Announcement.objects.all().order_by('-published_at')
    return render(request, 'government/announcements.html', {
        'announcements': announcements,
    })


@login_required
@government_required
def announcement_create_view(request):
    form = AnnouncementForm()
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.created_by = request.user
            if announcement.is_published and not announcement.published_at:
                announcement.published_at = timezone.now()
            announcement.save()
            messages.success(request, 'Announcement created successfully.')
            return redirect('government_announcements')
        messages.error(request, 'Please correct the errors below.')
    return render(request, 'government/announcement_form.html', {'form': form, 'announcement': None})


@login_required
@government_required
def announcement_edit_view(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    form = AnnouncementForm(instance=announcement)
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, instance=announcement)
        if form.is_valid():
            announcement = form.save(commit=False)
            if announcement.is_published and not announcement.published_at:
                announcement.published_at = timezone.now()
            announcement.save()
            messages.success(request, 'Announcement updated successfully.')
            return redirect('government_announcements')
        messages.error(request, 'Please correct the errors below.')
    return render(request, 'government/announcement_form.html', {'form': form, 'announcement': announcement})
