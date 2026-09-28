"""
URL configuration for awaaz_web project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve
import os

urlpatterns = [
	path('admin/', admin.site.urls),
	path('', include('complaints.urls')),
	re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
	re_path(r'^static_media/(?P<path>.*)$', serve, {'document_root': os.path.join(settings.BASE_DIR, 'media')}),
]
