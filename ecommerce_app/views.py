from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from .models import Product, UserProfile
from .forms import UserSignUpForm
# Create your views here.

def user_signup(request):
    if request.method == 'POST':
        form = UserSignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully!")
            return redirect('app:user_login')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserSignUpForm()

    return render(request, 'app/signup.html', {'form': form})




def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if not user.is_blocked:
                login(request, user)
                return redirect('app:index')
            else:
                messages.error(request, "Your account is blocked. Contact support.")
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'app/login.html')


def user_logout(request):
    logout(request)
    return redirect('app:user_login')


def index(request):
    return render(request, 'app/index.html')

def products(request):
    products = Product.objects.all()
    return render(request, 'app/products.html', {'products': products})
