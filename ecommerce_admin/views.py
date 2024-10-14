from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from ecommerce_app.models import UserProfile, Category
from .forms import UserProfileForm, LoginForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden

def superuser_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        return HttpResponseForbidden("You do not have permission to access this page.")
    return _wrapped_view


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('admin_dashboard')
            else:
                form.add_error(None, "Invalid credentials")
    else:
        form = LoginForm()
    return render(request, 'admin/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
@superuser_required
def index(request):
    return render(request, 'admin/index.html')

@login_required
@superuser_required
def user_list(request):
    users = UserProfile.objects.all()
    return render(request, 'admin/user_list.html', {'users': users})

@login_required
@superuser_required
def create_user(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('user_list')
    else:
        form = UserProfileForm()
    return render(request, 'admin/create_user.html', {'form': form})

@login_required
@superuser_required
def edit_user(request, user_id):
    user = get_object_or_404(UserProfile, id=user_id)
    if request.method == 'POST':
        user.email = request.POST.get('email', user.email)
        user.is_blocked = 'is_blocked' in request.POST
        user.save()
        return redirect('user_list')
    return render(request, 'admin/edit_user.html', {'user': user})


@login_required
@superuser_required
def categories_list(request):
    categories = Category.objects.all()
    return render(request, 'admin/categories_list.html', {'categories': categories})


@login_required
@superuser_required
def add_category(request):
    if request.method == "POST":
        category_name = request.POST.get('category_name')
        if category_name:
            Category.objects.create(name=category_name)
            messages.success(request, "Category added successfully!")
            return redirect('categories_list')
        else:
            messages.error(request, "Please enter a category name.")
    return render(request, 'admin/add_category.html')

@login_required
@superuser_required
def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == "POST":
        category_name = request.POST.get('name')
        if category_name:
            category.name = category_name
            category.save()
            messages.success(request, "Category updated successfully!")
            return redirect('categories_list')
        else:
            messages.error(request, "Please enter a category name.")
    return render(request, 'admin/edit_category.html', {'category': category})

@login_required
@superuser_required
def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == "POST":
        category.delete()
        messages.success(request, "Category deleted successfully!")
        return redirect('categories_list')
    return render(request, 'admin/delete_category.html', {'category': category})