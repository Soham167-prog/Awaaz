from django.shortcuts import render
from django.db.models import Count
from .models import Complaint

def landing_view(request):
    """Landing page with website introduction and stats"""
    
    # Get statistics
    total_reports = Complaint.objects.count()
    active_users = Complaint.objects.values('user').distinct().count()
    locations_covered = Complaint.objects.exclude(location='').values('location').distinct().count()
    severe_issues = Complaint.objects.filter(predicted_severity='severe').count()
    
    # Get recent reports for preview
    recent_reports = Complaint.objects.filter(public=True).order_by('-created_at')[:6]
    
    context = {
        'total_reports': total_reports,
        'active_users': active_users,
        'locations_covered': locations_covered,
        'severe_issues': severe_issues,
        'recent_reports': recent_reports,
    }
    
    return render(request, 'landing.html', context)


