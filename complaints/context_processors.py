from typing import Dict

from django.contrib.auth.models import AnonymousUser

from .models import UserProfile


def role_context(request) -> Dict[str, object]:
    """Inject role flags and notification metadata into templates."""
    user = getattr(request, "user", None)

    context = {
        "is_admin_user": False,
        "is_government_user": False,
        "has_unread_notifications": False,
        "unread_notifications_count": 0,
    }

    if not user or isinstance(user, AnonymousUser) or not user.is_authenticated:
        return context

    # Determine admin flag first (built-in staff/superuser roles)
    context["is_admin_user"] = bool(user.is_staff or user.is_superuser)

    # Ensure profile exists and fetch government flag
    profile, _ = UserProfile.objects.get_or_create(user=user)
    context["is_government_user"] = bool(profile.is_government_user)

    # Notifications (only counted for citizens/government users)
    notifications_qs = getattr(user, "notifications", None)
    if notifications_qs is not None:
        unread_qs = notifications_qs.filter(is_read=False)
        context["has_unread_notifications"] = unread_qs.exists()
        context["unread_notifications_count"] = unread_qs.count()

    return context
