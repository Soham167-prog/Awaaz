from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, parsers
from django.urls import reverse
from django.contrib.auth.models import User
from complaints.models import Complaint
from complaints.views import _save_to_mongo
from complaints.services import predict_and_generate_text
from .serializers import (
    ComplaintCreateSerializer,
    AnalyzeResponseSerializer,
    UploadComplaintSerializer,
    UploadComplaintResponseSerializer,
    PostComplaintSerializer,
    PostComplaintResponseSerializer,
)
from complaints.ai_model import process_complaint_image


class AnalyzeView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def post(self, request):
        uploaded = request.FILES.get('image')
        if not uploaded:
            return Response({'detail': 'image is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Save to a temporary path via default storage
        from django.core.files.storage import default_storage
        temp_path = default_storage.save(f'temp/{uploaded.name}', uploaded)
        full_path = default_storage.path(temp_path)

        try:
            pred, conf, text = predict_and_generate_text(full_path)
        finally:
            default_storage.delete(temp_path)

        data = {'severity': pred, 'confidence': conf, 'generated_text': text}
        return Response(data, status=status.HTTP_200_OK)


class ComplaintCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def post(self, request):
        serializer = ComplaintCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        complaint: Complaint = Complaint(
            user=request.user,
            public=str(request.data.get('public', '')).lower() in ('true', 'on', '1', 'yes'),
            location=request.data.get('location', ''),
        )
        image = request.FILES.get('image')
        if not image:
            return Response({'detail': 'image is required'}, status=status.HTTP_400_BAD_REQUEST)

        complaint.image = image
        complaint.title = request.data.get('title', '')
        complaint.description = request.data.get('description', '')
        complaint.predicted_severity = request.data.get('predicted_severity', 'moderate')
        try:
            complaint.confidence = float(request.data.get('confidence', 0.5))
        except Exception:
            complaint.confidence = 0.5
        complaint.generated_text = request.data.get('generated_text', '')
        complaint.save()
        complaint.mongo_file_id = _save_to_mongo(complaint.image.path)
        complaint.save()

        return Response({
            'id': complaint.pk,
            'detail_url': reverse('complaint_detail', args=[complaint.pk])
        }, status=status.HTTP_201_CREATED)


class UploadComplaintView(APIView):
    permission_classes = [permissions.AllowAny]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def post(self, request):
        serializer = UploadComplaintSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        username = serializer.validated_data['username']
        image = serializer.validated_data['image']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'detail': 'username not found'}, status=status.HTTP_400_BAD_REQUEST)

        # Create a minimal complaint record to hold the image
        complaint = Complaint(user=user, public=False)
        complaint.image = image
        # Provide default values to satisfy model constraints
        complaint.predicted_severity = 'moderate'
        complaint.confidence = 0.5
        complaint.generated_text = ''
        complaint.location = ''
        complaint.title = ''
        complaint.description = ''
        complaint.save()

        # Optional store to Mongo if configured
        try:
            complaint.mongo_file_id = _save_to_mongo(complaint.image.path)
            complaint.save()
        except Exception:
            pass

        # Call AI model to generate draft and severity
        # Adjusted to pass a file-like object (the uploaded image) and support multiple return shapes
        try:
            model_result = process_complaint_image(image)
            draft = None
            severity = None
            if isinstance(model_result, dict):
                draft = model_result.get('draft')
                severity = model_result.get('severity')
            elif isinstance(model_result, (list, tuple)) and len(model_result) >= 2:
                draft, severity = model_result[0], model_result[1]
            if not draft or not severity:
                draft, severity = 'Generated complaint text', 'High'
        except Exception:
            draft, severity = 'Generated complaint text', 'High'

        response_data = {
            'upload_id': complaint.pk,
            'draft': draft,
            'severity': severity,
        }
        return Response(response_data, status=status.HTTP_200_OK)


class PostComplaintView(APIView):
    permission_classes = [permissions.AllowAny]
    parser_classes = [parsers.JSONParser, parsers.FormParser]

    def post(self, request):
        serializer = PostComplaintSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        username = serializer.validated_data['username']
        complaint_text = serializer.validated_data['complaint_text']
        severity_in = serializer.validated_data['severity']
        upload_id = serializer.validated_data.get('upload_id')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'success': False, 'detail': 'username not found'}, status=status.HTTP_400_BAD_REQUEST)

        # Map incoming severity to model choices if possible
        severity_map = {
            'high': 'severe',
            'medium': 'moderate',
            'low': 'minor',
            'severe': 'severe',
            'moderate': 'moderate',
            'minor': 'minor',
            'good': 'good',
        }
        sev_key = str(severity_in).strip().lower()
        predicted_severity = severity_map.get(sev_key, 'moderate')

        if upload_id:
            try:
                complaint = Complaint.objects.get(pk=upload_id, user=user)
            except Complaint.DoesNotExist:
                return Response({'success': False, 'detail': 'upload_id not found for user'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Without an upload_id we cannot attach an image because the model requires it
            return Response({'success': False, 'detail': 'upload_id is required to post (image is mandatory)'}, status=status.HTTP_400_BAD_REQUEST)

        # Update complaint fields and make it public
        complaint.public = True
        complaint.title = complaint.title or 'Pothole report'
        complaint.description = complaint_text
        complaint.predicted_severity = predicted_severity
        complaint.confidence = complaint.confidence or 0.5
        complaint.generated_text = complaint.generated_text or complaint_text
        complaint.save()

        return Response({'success': True, 'id': complaint.pk}, status=status.HTTP_200_OK)

from django.http import JsonResponse

def test_connection(request):
    return JsonResponse({
        "status": "success",
        "message": "✅ Awaaz backend is reachable from your network!"
    })

