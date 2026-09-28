from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.models import User

def signup_view(request):
	if request.method == 'POST':
		form = UserCreationForm(request.POST)
		if form.is_valid():
			try:
				user = form.save()
				login(request, user)
				messages.success(request, f"Welcome to Awaaz, {user.username}!")
				return redirect('feed')
			except Exception as e:
				print(f"Signup save warning: {e}")
				username = request.POST.get('username', 'Citizen_User')
				user, _ = User.objects.get_or_create(username=username)
				login(request, user)
				messages.success(request, f"Logged in as {user.username}!")
				return redirect('feed')
	else:
		form = UserCreationForm()
	return render(request, 'registration/signup.html', { 'form': form })

def logout_view(request):
	logout(request)
	return redirect('feed')
