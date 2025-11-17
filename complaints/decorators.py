from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from .models import UserProfile


def _get_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def admin_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
            return view_func(request, *args, **kwargs)
        messages.error(request, 'Admin privileges required.')
        return redirect('login')

    return _wrapped


def government_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.is_staff or request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        profile = _get_profile(request.user)
        if profile.is_government_user:
            return view_func(request, *args, **kwargs)
        messages.error(request, 'Government access required.')
        return redirect('feed')

    return _wrapped


def citizen_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.is_staff or request.user.is_superuser:
            messages.error(request, 'Citizens only area.')
            return redirect('admin_dashboard')
        profile = _get_profile(request.user)
        if profile.is_government_user:
            messages.error(request, 'Citizens only area.')
            return redirect('government_dashboard')
        return view_func(request, *args, **kwargs)

    return _wrapped
