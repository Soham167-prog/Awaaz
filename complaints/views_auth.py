from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django import forms
from django.urls import reverse, reverse_lazy

from .models import UserProfile


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text='Required. Enter a valid email address.')
    
    class Meta:
        model = UserCreationForm.Meta.model
        fields = UserCreationForm.Meta.fields + ('email',)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['username'].widget.attrs.update({
            'class': 'w-full rounded-md bg-[#0f0f14] border border-[#2a2a36] p-3 focus:border-blue-500 focus:outline-none',
            'placeholder': 'Choose a username'
        })
        self.fields['email'].widget.attrs.update({
            'class': 'w-full rounded-md bg-[#0f0f14] border border-[#2a2a36] p-3 focus:border-blue-500 focus:outline-none',
            'placeholder': 'Enter your email address'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'w-full rounded-md bg-[#0f0f14] border border-[#2a2a36] p-3 focus:border-blue-500 focus:outline-none',
            'placeholder': 'Create a password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'w-full rounded-md bg-[#0f0f14] border border-[#2a2a36] p-3 focus:border-blue-500 focus:outline-none',
            'placeholder': 'Confirm your password'
        })
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # Create user profile
            UserProfile.objects.get_or_create(user=user)
        return user


class RoleBasedLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('role_redirect')


def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Account created successfully!')
            return redirect('role_redirect')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/signup.html', { 'form': form })


def logout_view(request):
    logout(request)
    return redirect('feed')


@login_required
def role_redirect_view(request):
    user = request.user

    if user.is_staff or user.is_superuser:
        return redirect('admin_dashboard')

    profile, _ = UserProfile.objects.get_or_create(user=user)
    if profile.is_government_user:
        return redirect('government_dashboard')

    return redirect('feed')


