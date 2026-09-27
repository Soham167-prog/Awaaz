from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm


def signup_view(request):
	if request.method == 'POST':
		form = UserCreationForm(request.POST)
		if form.is_valid():
			user = form.save()
			login(request, user)
			return redirect('feed')
	else:
		form = UserCreationForm()
	return render(request, 'registration/signup.html', { 'form': form })


def logout_view(request):
	logout(request)
	return redirect('feed')
