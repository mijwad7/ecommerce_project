from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from ecommerce_app.models import UserProfile, Category, Product, ProductImage, ProductSpec, Brand, ProductVariantImage, ProductVariant
from .forms import UserProfileForm, LoginForm, ProductForm, ProductSpecFormSet, ProductVariantForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.db.models import Q


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

def demo_login(request):
    user = authenticate(username='mijwad', password='1234')
    if user is not None:
        login(request, user)
        return redirect('admin_dashboard')  # Redirect to the main page after login
    else:
        # Handle case where demo user is not set up properly
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
        user.is_superuser = 'is_superuser' in request.POST
        user.is_active = 'is_active' in request.POST
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

@login_required
@superuser_required
def brands_list(request):
    brands = Brand.objects.all()
    return render(request, 'admin/brands_list.html', {'brands': brands})


@login_required
@superuser_required
def add_brand(request):
    if request.method == "POST":
        brand_name = request.POST.get('brand_name')
        if brand_name:
            Brand.objects.create(name=brand_name)
            messages.success(request, "Brand added successfully!")
            return redirect('brands_list')
        else:
            messages.error(request, "Please enter a brand name.")
    return render(request, 'admin/add_brand.html')

@login_required
@superuser_required
def edit_brand(request, brand_id):
    brand = get_object_or_404(Brand, id=brand_id)
    if request.method == "POST":
        brand_name = request.POST.get('name')
        if brand_name:
            brand.name = brand_name
            brand.save()
            messages.success(request, "Brand updated successfully!")
            return redirect('brands_list')
        else:
            messages.error(request, "Please enter a brand name.")
    return render(request, 'admin/edit_brand.html', {'brand': brand})

@login_required
@superuser_required
def delete_brand(request, brand_id):
    brand = get_object_or_404(Brand, id=brand_id)
    if request.method == "POST":
        brand.delete()
        messages.success(request, "Brand deleted successfully!")
        return redirect('brands_list')
    return render(request, 'admin/delete_brand.html', {'brand': brand})

@login_required
@superuser_required
def products_list(request):
    query = request.GET.get('query')
    category_id = request.GET.get('category')
    sort_by = request.GET.get('sort', 'id')
    products = Product.objects.all()

    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))

    if category_id:
        products = products.filter(category_id=category_id)

    if sort_by == 'name':
        products = products.order_by('name')
    elif sort_by == 'price':
        products = products.order_by('price')
    elif sort_by == 'category':
        products = products.order_by('category__name')
    else:
        products = products.order_by('id')

    return render(request, 'admin/products_list.html', {
        'products': products,
        'categories': Category.objects.all(),
    })


@login_required
@superuser_required
def add_product(request):
    if request.method == 'POST':
        product_form = ProductForm(request.POST, request.FILES)
        formset = ProductSpecFormSet(request.POST, instance=product_form.instance)

        if product_form.is_valid() and formset.is_valid():
            product = product_form.save()

            # Collect the uploaded images
            uploaded_images = request.FILES.getlist('images')

            # Check if there are at least 3 images
            if len(uploaded_images) < 3:
                product.delete()  # Remove the product if not enough images
                messages.error(request, 'You must upload at least 3 images.')
                return render(request, 'admin/add_product.html', {'product_form': product_form, 'formset': formset})

            # Save the images after validation
            for image in uploaded_images:
                ProductImage.objects.create(product=product, image=image)

            # Save the specifications
            formset.save()

            messages.success(request, 'Product added successfully!')
            return redirect('products_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        product_form = ProductForm()
        formset = ProductSpecFormSet()

    return render(request, 'admin/add_product.html', {'product_form': product_form, 'formset': formset})




@login_required
@superuser_required
def product_detail(request, product_id):
    product = get_object_or_404(Product.objects.all_objects(), id=product_id)
    specs = ProductSpec.objects.filter(product=product)
    variants = ProductVariant.objects.filter(product=product)
    return render(request, 'admin/product_detail.html', {
        'product': product,
        'specs': specs,
        'variants': variants
    })

@login_required
@superuser_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == "POST":
        product.delete()
        messages.success(request, "Product deleted successfully!")
        return redirect('products_list')
    return render(request, 'admin/delete_product.html', {'product': product})

@login_required
@superuser_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == "POST":
        product_form = ProductForm(request.POST, request.FILES, instance=product)

        if product_form.is_valid():
            product = product_form.save()
            uploaded_images = request.FILES.getlist('images')

            if uploaded_images:
                for image in uploaded_images:
                    ProductImage.objects.create(product=product, image=image)

            messages.success(request, "Product updated successfully!")
            return redirect('product_detail', product_id=product.id)

        else:
            messages.error(request, "Please correct the errors below.")

    else:
        product_form = ProductForm(instance=product)

    return render(request, 'admin/edit_product.html', {'product_form': product_form, 'product': product})

@login_required
@superuser_required
def add_product_variant(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        variant_form = ProductVariantForm(request.POST)
        uploaded_images = request.FILES.getlist('images')

        if variant_form.is_valid():
            variant = variant_form.save(commit=False)
            variant.product = product

            # Ensure at least 3 images are provided
            if len(uploaded_images) < 3:
                messages.error(request, 'Each variant must have at least 3 images.')
                return render(request, 'admin/add_product_variant.html', {'variant_form': variant_form})

            variant.save()

            # Save variant images
            for image in uploaded_images:
                ProductVariantImage.objects.create(variant=variant, image=image)

            messages.success(request, 'Product variant added successfully!')
            return redirect('product_detail', product_id=product.id)

        else:
            messages.error(request, 'Please correct the errors below.')

    else:
        variant_form = ProductVariantForm()

    return render(request, 'admin/add_product_variant.html', {
        'variant_form': variant_form,
        'product': product,
    })

# @login_required
# @superuser_required
# def view_product_variants(request, product_id):
#     product = get_object_or_404(Product, id=product_id)
#     variants = ProductVariant.objects.filter(product=product)
#     return render(request, 'admin/view_product_variants.html', {'product': product, 'variants': variants})

def product_variant_detail(request, variant_id):
    # Fetch the product variant using the ID
    variant = get_object_or_404(ProductVariant, id=variant_id)
    
    # Pass the variant details to the template
    context = {
        'variant': variant,
        'images': variant.images.all(),
    }
    return render(request, 'admin/variant_detail.html', context)

@login_required
@superuser_required
def edit_product_variant(request, variant_id):
    variant = get_object_or_404(ProductVariant, id=variant_id)
    product = variant.product  # Get the parent product

    if request.method == 'POST':
        variant_form = ProductVariantForm(request.POST, instance=variant)
        uploaded_images = request.FILES.getlist('images')

        if variant_form.is_valid():
            variant = variant_form.save()

            # If new images are uploaded, delete the old ones and save the new ones
            if uploaded_images:
                ProductVariantImage.objects.filter(variant=variant).delete()  # Delete existing images
                for image in uploaded_images:
                    ProductVariantImage.objects.create(variant=variant, image=image)

            messages.success(request, 'Product variant updated successfully!')
            return redirect('product_variant_detail', variant_id=variant.id)

        else:
            messages.error(request, 'Please correct the errors below.')

    else:
        variant_form = ProductVariantForm(instance=variant)

    return render(request, 'admin/edit_product_variant.html', {
        'variant_form': variant_form,
        'product': product,
        'variant': variant,
    })

@login_required
@superuser_required
def delete_product_variant(request, variant_id):
    variant = get_object_or_404(ProductVariant, id=variant_id)
    product = variant.product  # Get the parent product

    if request.method == 'POST':
        variant.delete()
        messages.success(request, 'Product variant deleted successfully!')
        return redirect('product_detail', product_id=product.id)

    return render(request, 'admin/delete_product_variant.html', {'variant': variant, 'product': product})



@login_required
@superuser_required
def view_deleted_products(request):
    products = Product.objects.all_objects().deleted()
    return render(request, 'admin/view_deleted_products.html', {'products': products})

@login_required
@superuser_required
def restore_product(request, product_id):
    product = get_object_or_404(Product.objects.all_objects(), id=product_id)
    if request.method == "POST":
        product.restore()
        product.save()
        messages.success(request, "Product restored successfully!")
        return redirect('products_list')
    return render(request, 'admin/view_deleted_products.html', {'product': product})

@login_required
@superuser_required
def view_deleted_categories(request):
    categories = Category.objects.all_objects().deleted()
    return render(request, 'admin/view_deleted_categories.html', {'categories': categories})

@login_required
@superuser_required
def restore_category(request, category_id):
    category = get_object_or_404(Category.objects.all_objects(), id=category_id)
    if request.method == "POST":
        category.restore()
        category.save()
        messages.success(request, "Category restored successfully!")
        return redirect('categories_list')
    return render(request, 'admin/view_deleted_categories.html', {'category': category})

@login_required
@superuser_required
def view_deleted_brands(request):
    brands = Brand.objects.all_objects().deleted()
    return render(request, 'admin/view_deleted_brands.html', {'brands': brands})

@login_required
@superuser_required
def restore_brand(request, brand_id):
    brand = get_object_or_404(Brand.objects.all_objects(), id=brand_id)
    if request.method == "POST":
        brand.restore()
        brand.save()
        messages.success(request, "Brand restored successfully!")
        return redirect('brands_list')
    return render(request, 'admin/view_deleted_brands.html', {'brand': brand})