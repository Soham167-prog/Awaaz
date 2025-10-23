from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from . import views_auth
from . import admin_views
from . import landing_views

urlpatterns = [
	path('', landing_views.landing_view, name='landing'),
	path('feed/', views.feed_view, name='feed'),
	path('new/', views.upload_view, name='upload'),
	path('complaint/<int:pk>/', views.detail_view, name='complaint_detail'),
	path('complaint/<int:pk>/upvote/', views.upvote_view, name='complaint_upvote'),
	path('complaint/<int:pk>/comment/', views.comment_create_view, name='complaint_comment'),
	path('complaint/<int:pk>/correct/', views.correct_severity_view, name='complaint_correct'),
	path('complaint/<int:pk>/edit/', views.edit_complaint_view, name='complaint_edit'),
	path('complaint/<int:pk>/delete/', views.delete_complaint_view, name='complaint_delete'),
	# admin
	path('admin/', admin_views.admin_login_view, name='admin_login'),
	path('admin/dashboard/', admin_views.admin_dashboard_view, name='admin_dashboard'),
	path('admin/complaint/<int:pk>/delete/', admin_views.admin_delete_complaint_view, name='admin_delete_complaint'),
	path('admin/logout/', admin_views.admin_logout_view, name='admin_logout'),
	# auth
	path('login/', auth_views.LoginView.as_view(template_name='registration/login.html', redirect_authenticated_user=True), name='login'),
	path('logout/', views_auth.logout_view, name='logout'),
	path('signup/', views_auth.signup_view, name='signup'),
]
