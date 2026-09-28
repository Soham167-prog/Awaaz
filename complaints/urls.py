from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from . import views_auth

urlpatterns = [
	path('', views.landing_view, name='landing'),
	path('feed/', views.feed_view, name='feed'),
	path('new/', views.upload_view, name='upload'),
	path('complaint/<int:pk>/', views.detail_view, name='complaint_detail'),
	path('complaint/<int:pk>/upvote/', views.upvote_view, name='complaint_upvote'),
	path('complaint/<int:pk>/comment/', views.comment_create_view, name='complaint_comment'),
	path('complaint/<int:pk>/correct/', views.correct_severity_view, name='complaint_correct'),
	path('complaint/<int:pk>/status/', views.update_status_view, name='update_status'),
	
	# Dashboards
	path('government/dashboard/', views.govt_dashboard_view, name='govt_dashboard'),
	path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
	
	# Recruiter Instant Demo Login Switcher
	path('demo-login/<str:role>/', views.demo_login_view, name='demo_login'),
	
	# Auth
	path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
	path('logout/', views_auth.logout_view, name='logout'),
	path('signup/', views_auth.signup_view, name='signup'),
]
