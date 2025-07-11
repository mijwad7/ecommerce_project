from decimal import Decimal

import paypalrestsdk
from currency_converter import CurrencyConverter
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import (authenticate, login, logout,
                                 update_session_auth_hash)
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache

from .forms import (AddressForm, CustomPasswordChangeForm, ReviewForm,
                    UserEditForm, UserSignUpForm)
from .models import (Address, Brand, Cart, CartProduct, Category,
                     CategoryOffer, Coupon, EmailOTPDevice, Notification,
                     Order, OrderItem, Product, ProductReturnRequest,
                     ProductSpec, ProductVariant, Review, Tag, UserProfile,
                     Wallet, Wishlist)
from .otp_utils import send_otp_to_email
from django.db import transaction
import requests


@never_cache
def user_signup(request):
    """
    Handles user signup. If the form is valid, creates a user and sends an OTP to their email.
    The user is disabled until the OTP is verified.
    """
    if request.method == "POST":
        form = UserSignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Disable account until OTP is verified
            user.save()
            send_otp_to_email(user)
            request.session["user_id"] = user.id
            messages.success(request, "Please check your email for an OTP.")
            return redirect("app:verify_otp")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserSignUpForm()

    return render(request, "app/signup.html", {"form": form})


def verify_otp(request):
    """
    Handles OTP verification for user sign up. If the OTP is valid, enables the user account and redirects to login.
    If the OTP is invalid or expired, shows an error message. If the user clicks the resend OTP button, sends a new OTP to
    their email and shows a success message.
    """
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


@never_cache
def user_login(request):
    if request.user.is_authenticated:
        return redirect("app:index")
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


@never_cache
def user_logout(request):
    logout(request)
    return redirect("app:user_login")

@never_cache
def index(request):
    featured_products = Product.objects.filter(is_featured=True)[:3]
    on_sale_products = Product.objects.filter(is_on_sale=True)[:3]
    recently_added_products = Product.objects.filter().order_by("-id")[:3]

    if request.user.is_authenticated:
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    else:
        wishlist = None

    return render(
        request,
        "app/index.html",
        {
            "featured_products": featured_products,
            "on_sale_products": on_sale_products,
            "recently_added_products": recently_added_products,
            "wishlist": wishlist,
        },
    )


def privacy_policy(request):
    return render(request, "app/privacy.html")


def terms_of_service(request):
    return render(request, "app/terms.html")


@never_cache
def products(request):
    """
    Lists all products with filtering and sorting options.

    Parameters:
        request.GET: query string parameters, including
            query: search query
            category: category name
            brand: brand id
            sort: sorting option, one of "id", "A-Z", "Z-A", "newest", "low-high", "high-low", "rating", "featured"
            tags: list of tag names

    Returns:
        rendered HTML page with products list
    """
    query = request.GET.get("query")
    category_name = request.GET.get("category")
    brand_id = request.GET.get("brand")
    sort = request.GET.get("sort", "id")
    selected_tags = request.GET.getlist("tags")

    categories = Category.objects.all()
    brands = Brand.objects.all()

    products = (
        Product.objects.select_related("category").prefetch_related("reviews").all()
    )

    if brand_id and Brand.objects.filter(id=brand_id).exists():
        products = products.filter(brand_id=brand_id)

    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    offer = None
    if category_name and Category.objects.filter(name=category_name).exists():
        products = products.filter(category__name=category_name)
        tags = Tag.objects.filter(category__name=category_name)
        offer = CategoryOffer.objects.filter(category__name=category_name, is_active=True).first()
    else:
        tags = Tag.objects.none()

    # Annotate with average ratings
    products = products.annotate(average_rating=Avg("reviews__rating"))

    if sort == "A-Z":
        products = products.order_by("name")
    elif sort == "available":
        products = products.filter(stock__gt=0)
    elif sort == "Z-A":
        products = products.order_by("-name")
    elif sort == "newest":
        products = products.order_by("-id")
    elif sort == "low-high":
        products = products.order_by("price")
    elif sort == "high-low":
        products = products.order_by("-price")
    elif sort == "rating":
        products = products.order_by("-average_rating")
    elif sort == "featured":
        products = products.filter(is_featured=True)

    if selected_tags:
        products = products.filter(tags__name__in=selected_tags).distinct()

    paginator = Paginator(products, 6)
    page_number = request.GET.get("page")
    paginated_products = paginator.get_page(page_number)

    if request.user.is_authenticated:
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    else:
        wishlist = None
    return render(
        request,
        "app/products.html",
        {
            "products": paginated_products,
            "categories": categories,
            "brands": brands,
            "tags": tags,
            "selected_tags": selected_tags,
            "offer": offer,
            "wishlist": wishlist,
        },
    )


@never_cache
def product_detail(request, product_id):
    """
    Product detail page.

    This view renders the product detail page with all its reviews, specifications, and related products.

    :param request: The request object
    :param product_id: The ID of the product to be displayed
    :return: The rendered HTML page
    """
    product = get_object_or_404(Product, id=product_id)

    reviews = Review.objects.filter(product=product)
    review_data = reviews.aggregate(avg_rating=Avg("rating"), num_reviews=Count("id"))

    review_score = (
        review_data["avg_rating"] if review_data["avg_rating"] is not None else 0
    )

    specs = ProductSpec.objects.filter(product=product)
    coupons = product.coupons.filter(is_active=True)

    related_products = (
        Product.objects.filter(tags__in=product.tags.all())
        .exclude(id=product.id)
        .distinct()[:4]
    )

    if related_products.count() < 4:
        additional_needed = 4 - related_products.count()
        additional_products = (
            Product.objects.filter(category=product.category)
            .exclude(id__in=related_products.values_list("id", flat=True))
            .exclude(id=product.id)[:additional_needed]
        )

        related_products = list(related_products) + list(additional_products)

    variants = ProductVariant.objects.filter(product=product)

    if request.user.is_authenticated:
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    else:
        wishlist = None

    return render(
        request,
        "app/product_detail.html",
        {
            "product": product,
            "reviews": reviews,
            "review_score": str(round(review_score, 1)),
            "num_reviews": review_data["num_reviews"],
            "specs": specs,
            "coupons": coupons,
            "related_products": related_products,
            "variants": variants,
            "wishlist": wishlist,
        },
    )


def get_variant_details(request, variant_id):
    """
    Returns a JSON response containing details about a specific product variant.

    The response contains the variant's price, sale price, whether it is on sale,
    the stock available, and a list of image URLs.

    Args:
        request (django.http.HttpRequest): The request object.
        variant_id (int): The ID of the product variant to get details about.

    Returns:
        django.http.JsonResponse: A JSON response containing the variant details.
    """
    variant = ProductVariant.objects.get(id=variant_id)
    images = [{"image_url": img.image.url} for img in variant.images.all()]

    data = {
        "price": variant.price,
        "sale_price": variant.sale_price,
        "is_on_sale": variant.is_on_sale,
        "stock": variant.stock,
        "images": images,
    }
    return JsonResponse(data)


def validate_cart(cart):
    """
    Validates all items in the cart.
    Returns a list of tuples: (invalid CartProduct, reason for invalidity).
    """
    invalid_items = []
    for cart_product in cart.cart_products.all():
        product = cart_product.product
        variant = cart_product.variant

        # Check if product is deleted
        if product.is_deleted:
            invalid_items.append((cart_product, f"Product {product.name} is no longer available."))
            continue

        # Check if category is deleted
        if product.category.is_deleted:
            invalid_items.append((cart_product, f"Category for {product.name} is no longer available."))
            continue

        # Check stock for product or variant
        available_stock = variant.stock if variant else product.stock
        if cart_product.quantity > available_stock:
            invalid_items.append((cart_product, f"Not enough stock for {product.name}. Available: {available_stock}."))
            continue

    return invalid_items

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    user = request.user

    cart, created = Cart.objects.get_or_create(user=user)

    quantity = int(request.POST.get("quantity", 1))
    variant_id = request.POST.get("variant_id")

    # Determine if we are adding a base product or a variant
    if variant_id:
        variant = get_object_or_404(ProductVariant, id=variant_id)

        if quantity > variant.stock:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Not enough stock available for this variant.",
                }
            )

        # Check if the variant is already in the cart
        cart_product, created = CartProduct.objects.get_or_create(
            cart=cart, product=product, variant=variant, defaults={"quantity": quantity}
        )
    else:
        if quantity > product.stock:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Not enough stock available for this product.",
                }
            )
        if quantity > product.max_per_user:
            return JsonResponse(
                {
                    "success": False,
                    "message": "You can only add up to "
                    + str(product.max_per_user)
                    + " items to your cart.",
                }
            )

        cart_product, created = CartProduct.objects.get_or_create(
            cart=cart, product=product, variant=None, defaults={"quantity": quantity}
        )

    # If the product or variant is already in the cart, increase the quantity (with validations)
    if not created:
        new_quantity = cart_product.quantity + quantity

        # Check the stock limits for variants or base products
        if variant_id:
            if new_quantity > variant.stock:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Not enough stock available for this variant.",
                    }
                )
            if new_quantity > product.max_per_user:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "You can only add up to "
                        + str(product.max_per_user)
                        + " items to your cart.",
                    }
                )
        else:
            if new_quantity > product.stock:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Not enough stock available for this product.",
                    }
                )

            if new_quantity > product.max_per_user:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "You can only add up to "
                        + str(product.max_per_user)
                        + " items to your cart.",
                    }
                )

        cart_product.quantity = new_quantity
        cart_product.save()

    return JsonResponse(
        {"success": True, "message": f"Added {product.name} to your cart."}
    )


@login_required
@never_cache
def view_cart(request):
    user = request.user

    try:
        cart = user.cart
        cart_products = cart.cart_products.all()
        total_price = cart.total_price
        # Validate cart and notify user of issues
        invalid_items = validate_cart(cart)
        if invalid_items:
            messages.warning(
                request,
                "Some items in your cart are no longer available. Please review and update your cart.",
            )
    except Cart.DoesNotExist:
        cart_products = []
        total_price = 0

    return render(
        request,
        "app/cart.html",
        {
            "cart_products": cart_products,
            "total_price": total_price,
        },
    )


@login_required
def remove_from_cart(request, cartproduct_id):
    cart_product = get_object_or_404(CartProduct, id=cartproduct_id)
    cart_product.delete()
    messages.success(
        request, f"{cart_product.product.name} has been removed from your cart."
    )
    return redirect("app:view_cart")


@login_required
def add_address(request):
    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, "Address added successfully!")
            next_page = request.GET.get("next", "app:view_profile")
            return redirect(next_page)
    else:
        form = AddressForm()

    return render(request, "app/add_address.html", {"form": form})

@login_required
def add_address_ajax(request):
    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            # Ensure address_type is set to 'shipping' if not provided
            if not address.address_type:
                address.address_type = "shipping"
            # If is_primary is checked, unset other primary addresses
            if address.is_primary:
                Address.objects.filter(user=request.user, is_primary=True).update(is_primary=False)
            address.save()
            return JsonResponse({
                "status": "success",
                "address": {
                    "id": address.id,
                    "line_1": address.line_1,
                    "line_2": address.line_2 or "",
                    "city": address.city,
                    "post_code": address.post_code,
                    "is_primary": address.is_primary,
                    "address_type": address.address_type
                }
            })
        return JsonResponse({"status": "error", "errors": form.errors}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)


@login_required
def edit_address(request, address_id):
    address = get_object_or_404(Address, id=address_id)
    if request.method == "POST":
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, "Address updated successfully!")
            return redirect("app:view_profile")
    else:
        form = AddressForm(instance=address)

    return render(request, "app/edit_address.html", {"form": form})


@login_required
def delete_address(request, address_id):
    address = get_object_or_404(Address, id=address_id)
    address.delete()
    messages.success(request, "Address deleted successfully!")
    return redirect("app:view_profile")


@never_cache
@login_required
def view_profile(request):
    username = request.user.username
    profile = get_object_or_404(UserProfile, username=username)
    addresses = profile.addresses.all()
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    return render(
        request,
        "app/view_profile.html",
        {"profile": profile, "addresses": addresses, "wallet": wallet},
    )


@login_required
def edit_profile(request):
    username = request.user.username
    profile = get_object_or_404(UserProfile, username=username)
    if request.method == "POST":
        form = UserEditForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect("app:view_profile")
    else:
        form = UserEditForm(instance=profile)

    return render(request, "app/edit_profile.html", {"form": form})


@login_required
def change_password(request):
    if request.method == "POST":
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            # Update the session to keep the user logged in after password change
            update_session_auth_hash(request, form.user)
            messages.success(request, "Your password was successfully updated!")
            return redirect("app:view_profile")
        else:
            messages.error(request, "Please correct the error below.")
    else:
        form = CustomPasswordChangeForm(user=request.user)

    return render(request, "app/change_password.html", {"form": form})

@login_required
@transaction.atomic
def checkout(request):
    user = request.user
    cart = get_object_or_404(Cart, user=user)
    addresses = Address.objects.filter(user=user, address_type="shipping")
    wallet, created = Wallet.objects.get_or_create(user=user)

    # Validate cart before proceeding
    invalid_items = validate_cart(cart)
    if invalid_items:
        for cart_product, _ in invalid_items:
            cart_product.delete()
        messages.error(request, "Some items in your cart are no longer available and have been removed. Please review your cart.")
        return redirect("app:view_cart")

    if request.method == "POST":
        coupon_code = request.POST.get("coupon_code")
        request.session["coupon_code"] = coupon_code
        use_wallet = request.POST.get("use_wallet", "off") == "on"
        wallet_deduction = 0
        discount = 0
        coupon = None

        if coupon_code:
            coupon = Coupon.objects.filter(code=coupon_code, is_active=True).first()
            if not coupon:
                messages.error(request, "Invalid or expired coupon.")
                coupon = None
            elif coupon.start_date > timezone.now() or coupon.end_date < timezone.now():
                messages.error(request, "Coupon is not currently valid.")
                coupon = None
            elif coupon in Order.objects.filter(user=user).values_list("applied_coupon", flat=True):
                messages.error(request, "You have already used this coupon.")
                coupon = None
            else:
                discount = min(cart.total_price * (coupon.discount_percent / 100), cart.total_price)

        # Calculate the discounted total after applying the coupon
        discounted_total = cart.total_price - discount

        if use_wallet:
            wallet_balance = wallet.balance
            if wallet_balance < 0:
                messages.error(request, "Invalid wallet balance.")
                return redirect("app:checkout")
            if wallet_balance >= discounted_total:
                wallet_deduction = discounted_total
                discounted_total = 0
                wallet.balance -= wallet_deduction
            else:
                wallet_deduction = wallet_balance
                discounted_total -= wallet_deduction
                wallet.balance = 0

        total_price = discounted_total
        if total_price < 0:
            messages.error(request, "Order total cannot be negative. Please review your cart or contact support.")
            return redirect("app:view_cart")

        address_id = request.POST.get("address")
        address = get_object_or_404(Address, id=address_id)
        request.session["selected_address_id"] = address_id
        request.session["wallet_deduction"] = float(wallet_deduction)
        request.session["total_price"] = float(total_price)  # Store INR total_price for consistency

        # If wallet covers the full amount, use WALLET payment method
        if use_wallet and total_price == 0:
            order = Order.objects.create(
                user=user,
                payment_method="WALLET",
                total_price=total_price,
                original_total_price=cart.total_price,
                wallet_deduction=wallet_deduction,
                applied_coupon=coupon,
                address_line_1=address.line_1,
                address_line_2=address.line_2,
                city=address.city,
                state=address.state,
                post_code=address.post_code,
            )
            for item in cart.cart_products.all():
                item.is_checked_out = True
                item.save()
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    price=item.total_price,
                    quantity=item.quantity,
                )
            wallet.save()
            cart.cart_products.all().delete()
            messages.success(request, "Order placed successfully using wallet balance!")
            return redirect("app:order_confirmation", order_id=order.id)

        # Otherwise, require a payment method for remaining balance
        payment_method = request.POST.get("payment_method")
        if not payment_method:
            messages.error(request, "Please select a payment method.")
            return redirect("app:checkout")

        if payment_method not in ["ONLINE", "COD"]:
            messages.error(request, "Invalid payment method.")
            return redirect("app:checkout")

        if payment_method == "ONLINE":
            # Fetch real-time INR to USD exchange rate
            try:
                response = requests.get(
                    f"https://v6.exchangerate-api.com/v6/{settings.EXCHANGE_RATE_API_KEY}/latest/INR"
                )
                response.raise_for_status()
                rate_data = response.json()
                if rate_data["result"] != "success":
                    raise ValueError("API error")
                exchange_rate = rate_data["conversion_rates"]["USD"]
                usd_amount = round(float(total_price) * exchange_rate * 0.97, 2)  # Add 2% buffer for PayPal spread
            except (requests.RequestException, ValueError, KeyError):
                messages.error(request, "Error fetching exchange rate. Please try again later.")
                return redirect("app:checkout")

            paypalrestsdk.configure(
                {
                    "mode": settings.PAYPAL_MODE,
                    "client_id": settings.PAYPAL_CLIENT_ID,
                    "client_secret": settings.PAYPAL_CLIENT_SECRET,
                }
            )
            payment = paypalrestsdk.Payment(
                {
                    "intent": "sale",
                    "payer": {"payment_method": "paypal"},
                    "redirect_urls": {
                        "return_url": f"https://{request.get_host()}{reverse('app:payment_complete')}",
                        "cancel_url": f"https://{request.get_host()}{reverse('app:checkout')}",
                    },
                    "transactions": [
                        {
                            "item_list": {
                                "items": [
                                    {
                                        "name": "Cart Purchase",
                                        "sku": "001",
                                        "price": str(usd_amount),
                                        "currency": "USD",
                                        "quantity": 1,
                                    }
                                ]
                            },
                            "amount": {"total": str(usd_amount), "currency": "USD"},
                            "description": "Purchase from Shophive",
                        }
                    ],
                }
            )
            if payment.create():
                for link in payment.links:
                    if link.rel == "approval_url":
                        approval_url = link.href
                        return redirect(approval_url)
            else:
                messages.error(request, "Error with PayPal payment.")
                return redirect("app:checkout")

        # Create order for COD or after PayPal redirect (handled in payment_complete)
        order = Order.objects.create(
            user=user,
            payment_method=payment_method,
            total_price=total_price,
            original_total_price=cart.total_price,
            wallet_deduction=wallet_deduction,
            applied_coupon=coupon,
            address_line_1=address.line_1,
            address_line_2=address.line_2,
            city=address.city,
            state=address.state,
            post_code=address.post_code,
        )
        for item in cart.cart_products.all():
            item.is_checked_out = True
            item.save()
            OrderItem.objects.create(
                order=order,
                product=item.product,
                price=item.total_price,
                quantity=item.quantity,
            )
        wallet.save()
        cart.cart_products.all().delete()
        messages.success(request, "Order placed successfully!")
        return redirect("app:order_confirmation", order_id=order.id)

    return render(request, "app/checkout.html", {"cart": cart, "addresses": addresses})

@login_required
def payment_complete(request):
    """
    Handles the completion of an online payment through PayPal.

    This function is called when the payment is successfully executed via PayPal. 
    It verifies the payment, creates an order and order items if the payment is 
    successful, and updates the wallet and cart accordingly. It also manages 
    session data related to the payment process and displays appropriate messages 
    to the user based on the payment outcome.

    Args:
        request (HttpRequest): The HTTP request object containing GET parameters 
                               `paymentId` and `PayerID` for payment verification.

    Returns:
        HttpResponse: Redirects to the order confirmation page if payment is 
                      successful, otherwise redirects back to the checkout page 
                      with an error message.
    """
    payment_id = request.GET.get("paymentId")
    payer_id = request.GET.get("PayerID")

    # Retrieve the payment
    payment = paypalrestsdk.Payment.find(payment_id)

    # Execute the payment
    if payment.execute({"payer_id": payer_id}):
        # Payment success, create the order and items
        user = request.user
        cart = get_object_or_404(Cart, user=user)

        # Validate cart before creating order
        invalid_items = validate_cart(cart)
        if invalid_items:
            for cart_product, _ in invalid_items:
                cart_product.delete()
            messages.error(request, "Some items in your cart are no longer available. Please review your cart.")
            return redirect("app:view_cart")

        address_id = request.session.get("selected_address_id")
        address = get_object_or_404(Address, id=address_id)
        coupon_code = request.session.get("coupon_code")
        wallet_deduction = request.session.get(
            "wallet_deduction", 0
        )  # Default to 0 if not in session
        wallet_deduction = Decimal(wallet_deduction)
        wallet, created = Wallet.objects.get_or_create(user=user)

        coupon = None
        if coupon_code:
            coupon = Coupon.objects.get(code=coupon_code)
            discount = cart.total_price * (coupon.discount_percent / 100)
            total_price = cart.total_price - discount
        else:
            total_price = cart.total_price

        if wallet_deduction > 0:
            total_price -= wallet_deduction
            wallet.balance -= wallet_deduction
            wallet.save()

        order = Order.objects.create(
            user=user,
            payment_method="ONLINE",
            total_price=total_price,
            original_total_price=cart.total_price if coupon else None,
            applied_coupon=coupon if coupon else None,
            address_line_1=address.line_1,
            address_line_2=address.line_2,
            city=address.city,
            state=address.state,
            post_code=address.post_code,
            wallet_deduction=wallet_deduction,
        )

        for item in cart.cart_products.all():
            item.is_checked_out = True
            item.save()
            OrderItem.objects.create(
                order=order,
                product=item.product,
                price=item.total_price,
                quantity=item.quantity,
            )

        cart.cart_products.all().delete()
        del request.session["selected_address_id"]
        del request.session["coupon_code"]
        del request.session["wallet_deduction"]

        messages.success(
            request, "Payment completed successfully! Your order has been placed."
        )
        return redirect("app:order_confirmation", order_id=order.id)
    else:
        messages.error(request, "Payment failed. Please try again.")
        return redirect("app:checkout")


@login_required
def apply_coupon(request):
    """
    View to apply a coupon to the current cart.

    If the coupon is valid and within its validity period, it will be applied to the cart and the new total will be returned as a JSON response.
    If the coupon is invalid or expired, an error message will be returned as a JSON response.
    If the user has already used the coupon, an error message will be returned as a JSON response.
    If the request method is not POST, an error message will be returned as a JSON response.

    Required parameters in the POST request:
        coupon_code: The code of the coupon to be applied

    Returns a JSON response with the following keys:
        status: A string indicating the status of the request ("success" or "error")
        message: An error message if the request was unsuccessful
        new_total: The new total of the cart if the request was successful
        discount: The discount amount if the request was successful
    """
    if request.method == "POST":
        coupon_code = request.POST.get("coupon_code")
        cart = get_object_or_404(Cart, user=request.user)

        # Check if the coupon exists, is active, and within the validity period
        coupon = Coupon.objects.filter(code=coupon_code, is_active=True).first()

        if coupon:
            if Order.objects.filter(user=request.user, applied_coupon=coupon).exists():
                return JsonResponse(
                    {"status": "error", "message": "You have already used this coupon."}
                )

            discount = cart.total_price * (coupon.discount_percent / 100)
            new_total = cart.total_price - discount

            request.session["coupon_code_to_remove"] = coupon.code
            return JsonResponse(
                {"status": "success", "new_total": new_total, "discount": discount}
            )

        return JsonResponse(
            {"status": "error", "message": "Invalid or expired coupon."}
        )

    return JsonResponse({"status": "error", "message": "Invalid request."})


@login_required
def remove_coupon(request):
    if request.method == "POST":
        coupon_code = request.session.get("coupon_code_to_remove")
        coupon = None

        if coupon_code:
            coupon = Coupon.objects.get(code=coupon_code)
            cart = get_object_or_404(Cart, user=request.user)

        if coupon:
            new_total = cart.total_price

            return JsonResponse(
                {
                    "status": "success",
                    "new_total": new_total,
                    "discount": 0,
                    "message": "Coupon removed successfully.",
                }
            )

        return JsonResponse({"status": "error", "message": "No coupon applied."})

    return JsonResponse({"status": "error", "message": "Invalid request."})


@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    return render(request, "app/order_confirmation.html", {"order": order})


@never_cache
@login_required
def view_orders(request):
    orders = Order.objects.filter(user=request.user).order_by("-id")

    return render(request, "app/view_orders.html", {"orders": orders})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    items = order.items.all()

    existing_requests = ProductReturnRequest.objects.filter(
        order_item__in=items
    ).values_list("order_item_id", flat=True)

    discount = None
    if order.original_total_price:
        wallet_deduction = order.wallet_deduction or 0
        discount = order.original_total_price - (order.total_price + wallet_deduction)

    return render(
        request,
        "app/order_detail.html",
        {
            "order": order,
            "items": items,
            "existing_requests": existing_requests,
            "discount": discount,
        },
    )


@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    wallet, created = Wallet.objects.get_or_create(user=request.user)

    if order.order_status in ["PENDING", "CONFIRMED"]:
        order.order_status = "CANCELLED"
        order.save()
        if order.payment_method == "ONLINE":
            wallet.add_funds(order.total_price)
            wallet.save()
            messages.success(request, "Order canceled successfully, payment refunded!")
        else:
            messages.success(request, "Order canceled successfully!")
    else:
        messages.error(request, "Order cannot be cancelled at this stage.")

    return redirect("app:view_orders")


@login_required
def update_cart_quantity(request, item_id):
    if request.method == "POST":
        item = get_object_or_404(CartProduct, id=item_id)

        product = item.product
        variant = item.variant  # May be None if it's a base product
        quantity = int(request.POST.get("quantity"))

        if variant:
            if quantity > variant.stock:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Not enough stock available for this variant.",
                    }
                )
        else:
            if quantity > product.stock:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Not enough stock available for this product.",
                    }
                )
            if quantity > product.max_per_user:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "You can only add up to "
                        + str(product.max_per_user)
                        + " items to your cart.",
                    }
                )

        # Update the quantity and recalculate the total price
        item.quantity = quantity
        item.save()

        # You may want to return the updated total price or any other info
        return JsonResponse({"success": True, "total_price": item.total_price})

    return JsonResponse({"error": "Invalid request"}, status=400)


@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    form = ReviewForm(request.POST)

    if form.is_valid():
        review = form.save(commit=False)
        review.product = product
        review.user = request.user
        review.save()
        messages.success(request, "Review added successfully!")
        return redirect("app:product_detail", product_id=product_id)
    else:
        messages.error(request, "Failed to add review. Please try again.")

    return render(
        request, "app/product_detail.html", {"product": product, "form": form}
    )


@login_required
def add_to_wishlist(request):
    if request.method == "POST":
        product_id = request.POST.get("product_id")
        product = get_object_or_404(Product, id=product_id)
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)

        if wishlist.products.filter(id=product_id).exists():
            return JsonResponse(
                {"status": "danger", "message": "Product is already in your wishlist."}
            )

        wishlist.products.add(product)
        return JsonResponse(
            {"status": "success", "message": "Product added to wishlist!"}
        )


@login_required
def remove_from_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist = Wishlist.objects.get(user=request.user)
    wishlist.products.remove(product)

    return redirect("app:wishlist")


@never_cache
@login_required
def wishlist(request):
    wishlist = Wishlist.objects.get(user=request.user)
    products = wishlist.products.all()

    return render(
        request, "app/wishlist.html", {"wishlist": wishlist, "products": products}
    )


@login_required
def return_request(request, order_item_id):
    order_item = get_object_or_404(OrderItem, id=order_item_id)

    if request.method == "POST":
        order = order_item.order
        product = order_item.product
        reason = request.POST.get("reason")

        # Calculate refund amount based on any order discount
        if order.original_total_price and order.original_total_price > 0:
            discount_ratio = order.total_price / order.original_total_price
        else:
            discount_ratio = Decimal(1)  # No discount

        # Adjust the item's price with the discount ratio
        item_price_after_discount = order_item.price * discount_ratio
        refund_amount = item_price_after_discount * order_item.quantity

        ProductReturnRequest.objects.create(
            user=request.user,
            order_item=order_item,
            reason=reason,
            refund_amount=refund_amount,
        )

        messages.success(request, "Your return request has been submitted.")

        return redirect("app:order_detail", order_id=order_item.order.id)

    return redirect("app:order_detail", order_id=order_item.order.id)


@login_required
def return_request_list(request):
    return_requests = ProductReturnRequest.objects.filter(user=request.user).order_by(
        "-requested_at"
    )
    return render(
        request, "app/return_request_list.html", {"return_requests": return_requests}
    )


@login_required
def user_notifications(request):
    user = request.user
    notifications = (
        Notification.objects.filter(user=user, is_read=False)
        .order_by("-created_at")
        .values("id", "message", "created_at", "action_url")
    )
    return JsonResponse(list(notifications), safe=False)


@login_required
def mark_notification_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id)
    notification.is_read = True
    notification.save()
    return JsonResponse({"success": True})

def wishlist_toggle(request):
    if request.method == "POST":
        product_id = request.POST.get("product_id")
        product = get_object_or_404(Product, id=product_id)
        user = request.user

        wishlist, created = Wishlist.objects.get_or_create(user=user)

        if product in wishlist.products.all():
            # If already in wishlist, remove it
            wishlist.products.remove(product)
            return JsonResponse({"status": "success", "action": "remove"})
        else:
            # Add to wishlist
            wishlist.products.add(product)
            return JsonResponse({"status": "success", "action": "add"})

    return JsonResponse({"status": "error", "message": "Invalid request"})

