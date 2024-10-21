from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from .models import Product, UserProfile, EmailOTPDevice, Review, ProductSpec, Category, ProductVariant
from .forms import UserSignUpForm
from .otp_utils import send_otp_to_email
from django.db.models import Avg, Count, Q
from django.utils import timezone
from django.http import JsonResponse


def user_signup(request):
    if request.method == "POST":
        form = UserSignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Disable account until OTP is verified
            user.save()
            send_otp_to_email(user)  # Send OTP
            request.session["user_id"] = user.id  # Store user ID in session
            messages.success(request, "Please check your email for an OTP.")
            return redirect("app:verify_otp")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserSignUpForm()

    return render(request, "app/signup.html", {"form": form})


def verify_otp(request):
    if request.method == "POST":
        if "resend_otp" in request.POST:
            user_id = request.session.get("user_id")
            if not user_id:
                messages.error(request, "Session expired. Please sign up again.")
                return redirect("app:signup")

            user = get_object_or_404(UserProfile, id=user_id)
            if send_otp_to_email(user, force_resend=True):
                messages.success(request, "A new OTP has been sent to your email.")
            else:
                messages.error(request, "Could not resend OTP. Please try again.")
            return redirect("app:verify_otp")

        otp = request.POST.get("otp")
        user_id = request.session.get("user_id")
        if not user_id:
            messages.error(request, "Session expired. Please sign up again.")
            return redirect("app:signup")

        user = get_object_or_404(UserProfile, id=user_id)
        device = EmailOTPDevice.objects.filter(user=user).first()

        if device and device.verify_otp(otp):
            user.is_active = True
            user.save()
            messages.success(request, "Your account has been verified!")
            return redirect("app:user_login")
        else:
            messages.error(request, "Invalid or expired OTP. Please try again.")

    return render(request, "app/verify_otp.html")


def user_login(request):
    if request.user.is_authenticated:
        return redirect('app:index')
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if not user.is_blocked:
                login(request, user)
                return redirect("app:index")
            else:
                messages.error(request, "Your account is blocked. Contact support.")
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, "app/login.html")


def user_logout(request):
    logout(request)
    return redirect("app:user_login")

def demo_login(request):
    user = authenticate(username='mijwad', password='1234')
    if user is not None:
        login(request, user)
        return redirect('app:index')
    else:
        return redirect('login')

def index(request):
    featured_products = Product.objects.filter(is_featured=True)[:3]
    on_sale_products = Product.objects.filter(is_on_sale=True)[:3]
    recently_added_products = Product.objects.filter().order_by('-id')[:3]

    return render(request, "app/index.html", {
        'featured_products': featured_products,
        'on_sale_products': on_sale_products,
        'recently_added_products': recently_added_products
    })


def products(request):
    query = request.GET.get('query')
    category_id = request.GET.get('category')
    products = Product.objects.all().order_by('id')
    categories = Category.objects.all()

    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))

    if category_id:
        products = products.filter(category_id=category_id)

    for product in products:
        average_rating = product.reviews.aggregate(Avg('rating'))['rating__avg']
        product.average_rating = average_rating if average_rating is not None else 0

    return render(request, "app/products.html", {
        "products": products,
        "categories": categories
    })


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # Fetch reviews and use aggregation for the average rating and review count
    reviews = Review.objects.filter(product=product)
    review_data = reviews.aggregate(avg_rating=Avg("rating"), num_reviews=Count("id"))

    # Safely handle case when there are no reviews
    review_score = (
        review_data["avg_rating"] if review_data["avg_rating"] is not None else 0
    )

    specs = ProductSpec.objects.filter(product=product)
    coupons = product.coupons.filter(start_date__lte=timezone.now(), end_date__gte=timezone.now())

    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]

    variants = ProductVariant.objects.filter(product=product)


    return render(
        request,
        "app/product_detail.html",
        {
            "product": product,
            "reviews": reviews,
            "review_score": round(review_score, 1),
            "num_reviews": review_data["num_reviews"],
            "specs": specs,
            "coupons": coupons,
            "related_products": related_products,
            "variants": variants
        },
    )

def get_variant_details(request, variant_id):
    variant = ProductVariant.objects.get(id=variant_id)
    images = [{'image_url': img.image.url} for img in variant.images.all()]  # Fetching variant images

    data = {
        'price': variant.price,
        'sale_price': variant.sale_price,
        'is_on_sale': variant.is_on_sale,
        'stock': variant.stock,
        'images': images,
    }
    return JsonResponse(data)