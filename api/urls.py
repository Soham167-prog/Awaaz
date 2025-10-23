from django.urls import path
from .views import (
    AnalyzeView,
    ComplaintCreateView,
    UploadComplaintView,
    PostComplaintView,
    test_connection,
)

# Single urlpatterns list that includes ALL API endpoints
urlpatterns = [
    path('test/', test_connection, name='test_connection'),
    path('analyze/', AnalyzeView.as_view(), name='api_analyze'),
    path('complaints/', ComplaintCreateView.as_view(), name='api_complaint_create'),
    path('upload_complaint/', UploadComplaintView.as_view(), name='api_upload_complaint'),
    path('post_complaint/', PostComplaintView.as_view(), name='api_post_complaint'),
]