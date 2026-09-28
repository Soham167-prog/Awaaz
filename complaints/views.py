from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import login, logout
from django.contrib import messages
from django.core.paginator import Paginator
from .forms import ComplaintForm, CommentForm, SeverityCorrectionForm
from .models import Complaint, Comment

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
	try:
		client = MongoClient(uri)
		db = client.get_database()
		fs = GridFS(db)
		with open(path, 'rb') as f:
			file_id = fs.put(f, filename=path.split('/')[-1])
		return str(file_id)
	except Exception:
		return ''


def landing_view(request):
	total_complaints = Complaint.objects.count()
	recent_complaints = Complaint.objects.filter(public=True).order_by('-created_at')[:3]
	pending_count = Complaint.objects.filter(status='pending').count()
	resolved_count = Complaint.objects.filter(status='resolved').count()
	
	return render(request, 'complaints/landing.html', {
		'total_complaints': total_complaints,
		'recent_complaints': recent_complaints,
		'pending_count': pending_count,
		'resolved_count': resolved_count,
	})


def feed_view(request):
	qs = Complaint.objects.filter(public=True)
	severity = request.GET.get('severity')
	if severity in {'minor', 'moderate', 'severe'}:
		qs = qs.filter(predicted_severity=severity)
	status = request.GET.get('status')
	if status in {'pending', 'in_progress', 'resolved'}:
		qs = qs.filter(status=status)
	q = request.GET.get('q')
	if q:
		qs = qs.filter(title__icontains=q) | qs.filter(description__icontains=q)
	sort = request.GET.get('sort')
	if sort == 'top':
		qs = sorted(qs, key=lambda c: c.upvote_count, reverse=True)
	else:
		qs = qs.order_by('-created_at')
	p = Paginator(qs, 9)
	page = request.GET.get('page')
	items = p.get_page(page)
	return render(request, 'complaints/feed.html', { 'items': items })


@login_required
def upload_view(request):
	if request.method == 'POST':
		uploaded = request.FILES.get('image')
		if not uploaded:
			messages.error(request, 'Please choose an image to upload.')
			return render(request, 'complaints/upload.html', {'form': ComplaintForm()})
		public_flag = bool(request.POST.get('public'))
		complaint = Complaint(user=request.user, public=public_flag)
		complaint.image = uploaded
		complaint.save()
		
		# Generate prediction & complaint text
		from .services import predict_and_generate_text
		pred, conf, text = predict_and_generate_text(complaint.image.path)
		complaint.predicted_severity = pred
		complaint.confidence = conf
		complaint.generated_text = text
		complaint.mongo_file_id = _save_to_mongo(complaint.image.path)
		complaint.save()
		messages.success(request, 'Grievance submitted successfully!')
		return redirect('complaint_detail', pk=complaint.pk)
	return render(request, 'complaints/upload.html', {'form': ComplaintForm()})


def detail_view(request, pk: int):
	obj = get_object_or_404(Complaint, pk=pk)
	comment_form = CommentForm()
	corr_form = SeverityCorrectionForm(instance=obj)
	return render(request, 'complaints/detail.html', {
		'obj': obj,
		'comment_form': comment_form,
		'corr_form': corr_form
	})


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
			
			# Check role tags
			role = request.session.get('user_role', '')
			if request.user.is_superuser or role == 'admin' or request.user.username == 'admin':
				c.is_admin_response = True
			elif request.user.is_staff or role == 'govt' or 'govt' in request.user.username.lower():
				c.is_govt_response = True
				
			c.save()
			messages.success(request, 'Comment published!')
	return redirect('complaint_detail', pk=pk)


@login_required
def correct_severity_view(request, pk: int):
	obj = get_object_or_404(Complaint, pk=pk)
	if request.method == 'POST':
		form = SeverityCorrectionForm(request.POST, instance=obj)
		if form.is_valid():
			form.save()
			messages.success(request, 'Ground-truth severity correction recorded!')
	return redirect('complaint_detail', pk=pk)


@login_required
def update_status_view(request, pk: int):
	"""Update grievance resolution status (Government / Admin action)"""
	obj = get_object_or_404(Complaint, pk=pk)
	if request.method == 'POST':
		new_status = request.POST.get('status')
		if new_status in {'pending', 'in_progress', 'resolved'}:
			obj.status = new_status
			obj.save()
			messages.success(request, f"Complaint status updated to {new_status.replace('_', ' ').title()}.")
	return redirect('complaint_detail', pk=pk)


def govt_dashboard_view(request):
	"""Government Official Municipal Dashboard"""
	complaints = Complaint.objects.all().order_by('-created_at')
	total_count = complaints.count()
	pending_count = complaints.filter(status='pending').count()
	in_progress_count = complaints.filter(status='in_progress').count()
	resolved_count = complaints.filter(status='resolved').count()
	severe_count = complaints.filter(predicted_severity='severe').count()

	return render(request, 'complaints/govt_dashboard.html', {
		'complaints': complaints[:15],
		'total_count': total_count,
		'pending_count': pending_count,
		'in_progress_count': in_progress_count,
		'resolved_count': resolved_count,
		'severe_count': severe_count,
	})


def admin_dashboard_view(request):
	"""System Administrator Health & Governance Dashboard"""
	complaints = Complaint.objects.all().order_by('-created_at')
	total_users = User.objects.count()
	total_comments = Comment.objects.count()

	return render(request, 'complaints/admin_dashboard.html', {
		'complaints': complaints[:10],
		'total_users': total_users,
		'total_complaints': complaints.count(),
		'total_comments': total_comments,
	})


def demo_login_view(request, role: str):
	"""Instant Recruiter Demo Login Switcher (Citizen, Government Official, System Admin)"""
	if role == 'govt':
		user, _ = User.objects.get_or_create(username='Govt_PWD_Official', defaults={'email': 'pwd@awaaz.gov.in', 'is_staff': True})
		user.is_staff = True
		user.save()
		request.session['user_role'] = 'govt'
		login(request, user)
		messages.success(request, "Logged in as Government PWD Official.")
		return redirect('govt_dashboard')

	elif role == 'admin':
		user, _ = User.objects.get_or_create(username='System_Admin', defaults={'email': 'admin@awaaz.gov.in', 'is_superuser': True, 'is_staff': True})
		user.is_superuser = True
		user.is_staff = True
		user.save()
		request.session['user_role'] = 'admin'
		login(request, user)
		messages.success(request, "Logged in as System Administrator.")
		return redirect('admin_dashboard')

	else: # citizen
		user, _ = User.objects.get_or_create(username='Citizen_DemoUser', defaults={'email': 'citizen@awaaz.org'})
		request.session['user_role'] = 'citizen'
		login(request, user)
		messages.success(request, "Logged in as Citizen User.")
		return redirect('feed')
