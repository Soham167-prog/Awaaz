from django.urls import path
from . import views
from . import views_auth
from . import admin_views
from . import landing_views
from . import government_views

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
	path('complaint/<int:pk>/report/', views.report_complaint_view, name='complaint_report'),
	path('complaint/<int:pk>/resolve/', views.mark_complaint_resolved_view, name='complaint_resolve'),
	path('notifications/', views.notifications_view, name='notifications'),
	path('announcements/', views.announcements_view, name='announcements'),
	# government portal
	path('gov/', government_views.dashboard_view, name='government_dashboard'),
	path('gov/complaints/<int:pk>/', government_views.complaint_detail_view, name='government_complaint_detail'),
	path('gov/announcements/', government_views.announcements_view, name='government_announcements'),
	path('gov/announcements/new/', government_views.announcement_create_view, name='government_announcement_create'),
	path('gov/announcements/<int:pk>/delete/', government_views.announcement_delete_view, name='government_announcement_delete'),
	# role-based auth
	path('login/', views_auth.RoleBasedLoginView.as_view(), name='login'),
	path('role-redirect/', views_auth.role_redirect_view, name='role_redirect'),
	path('logout/', views_auth.logout_view, name='logout'),
	path('signup/', views_auth.signup_view, name='signup'),
	# custom admin panel
	path('custom-admin/', admin_views.admin_login_view, name='admin_login'),
	path('custom-admin/dashboard/', admin_views.admin_dashboard_view, name='admin_dashboard'),
	path('custom-admin/complaint/<int:pk>/delete/', admin_views.admin_delete_complaint_view, name='admin_delete_complaint'),
	path('custom-admin/reports/', admin_views.admin_reports_view, name='admin_reports'),
	path('custom-admin/reports/<int:pk>/', admin_views.admin_report_detail_view, name='admin_report_detail'),
	path('custom-admin/government-users/', admin_views.admin_government_users_view, name='admin_government_users'),
	path('custom-admin/government-users/create/', admin_views.admin_create_government_user_view, name='admin_create_government_user'),
	path('custom-admin/logout/', admin_views.admin_logout_view, name='admin_logout'),
]
