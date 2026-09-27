from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .forms import ComplaintForm, CommentForm, SeverityCorrectionForm
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
		# Accept raw POST to avoid form validation issues
		uploaded = request.FILES.get('image')
		if not uploaded:
			messages.error(request, 'Please choose an image to upload.')
			return render(request, 'complaints/upload.html', {'form': ComplaintForm()})
		public_flag = bool(request.POST.get('public'))
		complaint = Complaint(user=request.user, public=public_flag)
		complaint.image = uploaded
		complaint.save()  # saves file to disk
		pred, conf, text = predict_and_generate_text(complaint.image.path)
		complaint.predicted_severity = pred
		complaint.confidence = conf
		complaint.generated_text = text
		complaint.mongo_file_id = _save_to_mongo(complaint.image.path)
		complaint.save()
		messages.success(request, 'Complaint submitted successfully!')
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
