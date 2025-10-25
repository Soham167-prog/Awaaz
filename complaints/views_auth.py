from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django import forms
from django.urls import reverse


class CustomUserCreationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add custom CSS classes to form fields
        self.fields['username'].widget.attrs.update({
            'class': 'w-full rounded-md bg-[#0f0f14] border border-[#2a2a36] p-3 focus:border-blue-500 focus:outline-none',
            'placeholder': 'Choose a username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'w-full rounded-md bg-[#0f0f14] border border-[#2a2a36] p-3 focus:border-blue-500 focus:outline-none',
            'placeholder': 'Create a password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'w-full rounded-md bg-[#0f0f14] border border-[#2a2a36] p-3 focus:border-blue-500 focus:outline-none',
            'placeholder': 'Confirm your password'
        })


def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Account created successfully!')
            return redirect('feed')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/signup.html', { 'form': form })


def logout_view(request):
    logout(request)
    return redirect('feed')


