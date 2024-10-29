from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from .models import (
    Product,
    UserProfile,
    EmailOTPDevice,
    Review,
    ProductSpec,
    Category,
    ProductVariant,
    Cart,
    CartProduct,
    Address,
    Brand,
    Order,
    OrderItem,
    Tag,
    Wishlist
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from .forms import UserSignUpForm, AddressForm, UserEditForm, CustomPasswordChangeForm, ReviewForm
from .otp_utils import send_otp_to_email
from django.db.models import Avg, Count, Q
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.paginator import Paginator
import paypalrestsdk
from django.conf import settings
from django.urls import reverse
from currency_converter import CurrencyConverter



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


def user_logout(request):
    logout(request)
    return redirect("app:user_login")


def demo_login(request):
    user = authenticate(username="mijwad", password="1234")
    if user is not None:
        login(request, user)
        return redirect("app:index")
    else:
        return redirect("login")


def index(request):
    featured_products = Product.objects.filter(is_featured=True)[:3]
    on_sale_products = Product.objects.filter(is_on_sale=True)[:3]
    recently_added_products = Product.objects.filter().order_by("-id")[:3]

    return render(
        request,
        "app/index.html",
        {
            "featured_products": featured_products,
            "on_sale_products": on_sale_products,
            "recently_added_products": recently_added_products,
        },
    )


def products(request):
    query = request.GET.get("query")
    category_id = request.GET.get("category")
    brand_id = request.GET.get("brand")
    sort = request.GET.get("sort", "id")
    selected_tags = request.GET.getlist('tags')

    # Fetch categories and brands as before
    categories = Category.objects.all()
    brands = Brand.objects.all()

    # Pre-select related data to optimize queries
    products = (
        Product.objects.select_related("category").prefetch_related("reviews").all()
    )

    # Filter by brand (only if valid)
    if brand_id and Brand.objects.filter(id=brand_id).exists():
        products = products.filter(brand_id=brand_id)

    # Filter by search query
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    # Filter by category (only if valid)
    if category_id and Category.objects.filter(id=category_id).exists():
        products = products.filter(category_id=category_id)
        tags = Tag.objects.filter(category_id=category_id)  # Only get tags for this category
    else:
        tags = Tag.objects.none()  # No tags if no category is selected

    # Annotate with average ratings
    products = products.annotate(average_rating=Avg("reviews__rating"))

    # Handle sorting
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

    # Pagination (10 products per page)
    paginator = Paginator(products, 6)
    page_number = request.GET.get("page")
    paginated_products = paginator.get_page(page_number)

    return render(
        request,
        "app/products.html",
        {
            "products": paginated_products,
            "categories": categories,
            "brands": brands,
            "tags": tags,
            "selected_tags": selected_tags
        },
    )


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
    coupons = product.coupons.filter(
        start_date__lte=timezone.now(), end_date__gte=timezone.now()
    )

    related_products = Product.objects.filter(category=product.category).exclude(
        id=product.id
    )[:4]

    variants = ProductVariant.objects.filter(product=product)

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
        },
    )


def get_variant_details(request, variant_id):
    variant = ProductVariant.objects.get(id=variant_id)
    images = [
        {"image_url": img.image.url} for img in variant.images.all()
    ]  # Fetching variant images

    data = {
        "price": variant.price,
        "sale_price": variant.sale_price,
        "is_on_sale": variant.is_on_sale,
        "stock": variant.stock,
        "images": images,
    }
    return JsonResponse(data)


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    user = request.user

    # Check if the user has a cart; create one if not
    cart, created = Cart.objects.get_or_create(user=user)

    # Get the quantity and variant ID from the AJAX request
    quantity = int(request.POST.get("quantity", 1))
    variant_id = request.POST.get("variant_id")

    # Determine if we are adding a base product or a variant
    if variant_id:
        variant = get_object_or_404(ProductVariant, id=variant_id)

        # Validate the requested quantity against the variant's stock
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
        # Validate the requested quantity against the base product's stock
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
                    "message": "You can only add up to " + str(product.max_per_user) + " items to your cart.",
                }
            )

        # Check if the base product is already in the cart
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
                        "message": "You can only add up to " + str(product.max_per_user) + " items to your cart.",
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
                        "message": "You can only add up to " + str(product.max_per_user) + " items to your cart.",
                    }
                )

        # Update the cart product quantity
        cart_product.quantity = new_quantity
        cart_product.save()

    # Return success response
    return JsonResponse(
        {"success": True, "message": f"Added {product.name} to your cart."}
    )


@login_required
def view_cart(request):
    user = request.user

    # Fetch the user's cart; if no cart exists, it will show an empty cart
    try:
        cart = user.cart
        cart_products = cart.cart_products.all()
        total_price = cart.total_price
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
            return redirect("app:view_profile")
    else:
        form = AddressForm()

    return render(request, "app/add_address.html", {"form": form})


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


@login_required
def view_profile(request):
    username = request.user.username
    profile = get_object_or_404(UserProfile, username=username)
    addresses = profile.addresses.all()
    return render(
        request, "app/view_profile.html", {"profile": profile, "addresses": addresses}
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


import paypalrestsdk
from django.conf import settings

@login_required
def checkout(request):
    user = request.user
    cart = get_object_or_404(Cart, user=user)
    addresses = Address.objects.filter(user=user, address_type='shipping')
    c = CurrencyConverter()
    usd_amount = round(c.convert(cart.total_price, 'INR', 'USD'), 2)

    if request.method == "POST":
        address_id = request.POST.get("address")
        address = get_object_or_404(Address, id=address_id)
        request.session['selected_address_id'] = address_id
        payment_method = request.POST.get("payment_method")

        if not payment_method:
            messages.error(request, "Please select a payment method.")
            return redirect("app:checkout")

        if not address:
            messages.error(request, "Please select an address.")
            return redirect("app:checkout")

        if payment_method == "ONLINE":
            # Configure PayPal SDK
            paypalrestsdk.configure({
                "mode": settings.PAYPAL_MODE,
                "client_id": settings.PAYPAL_CLIENT_ID,
                "client_secret": settings.PAYPAL_CLIENT_SECRET
            })

            # Create the PayPal payment
            payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {
                    "payment_method": "paypal"
                },
                "redirect_urls": {
                    "return_url": request.build_absolute_uri(reverse("app:payment_complete")),
                    "cancel_url": request.build_absolute_uri(reverse("app:checkout")),
                },
                "transactions": [{
                    "item_list": {
                        "items": [{
                            "name": "Cart Purchase",
                            "sku": "001",
                            "price": str(usd_amount),
                            "currency": "USD",
                            "quantity": 1
                        }]
                    },
                    "amount": {
                        "total": str(usd_amount),
                        "currency": "USD"
                    },
                    "description": "Purchase from My Django Store"
                }]
            })

            if payment.create():
                for link in payment.links:
                    if link.rel == "approval_url":
                        approval_url = link.href
                        return redirect(approval_url)
            else:
                messages.error(request, "Error with PayPal payment.")
                return redirect("app:checkout")

        # Proceed with Cash on Delivery payment method
        order = Order.objects.create(
            user=user,
            address=address,
            payment_method=payment_method,
            total_price=cart.total_price,
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
        messages.success(request, "Order placed successfully!")
        return redirect("app:order_confirmation", order_id=order.id)

    return render(request, "app/checkout.html", {"cart": cart, "addresses": addresses})

@login_required
def payment_complete(request):
    payment_id = request.GET.get("paymentId")
    payer_id = request.GET.get("PayerID")

    # Retrieve the payment
    payment = paypalrestsdk.Payment.find(payment_id)

    # Execute the payment
    if payment.execute({"payer_id": payer_id}):
        # Payment success, create the order and items
        user = request.user
        cart = get_object_or_404(Cart, user=user)
        address_id = request.session.get("selected_address_id")
        address = get_object_or_404(Address, id=address_id)
        
        order = Order.objects.create(
            user=user,
            address=address,
            payment_method="ONLINE",
            total_price=cart.total_price,
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
        messages.success(request, "Payment completed successfully! Your order has been placed.")
        return redirect("app:order_confirmation", order_id=order.id)
    else:
        messages.error(request, "Payment failed. Please try again.")
        return redirect("app:checkout")


@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    return render(request, "app/order_confirmation.html", {"order": order})


@login_required
def view_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-id')

    return render(request, "app/view_orders.html", {"orders": orders})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    items = order.items.all()

    return render(request, "app/order_detail.html", {"order": order, "items": items})


@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.order_status in ["PENDING", "CONFIRMED"]:
        order.order_status = "CANCELLED"
        order.save()
        messages.success(request, "Order canceled successfully!")
    else:
        messages.error(request, "Order cannot be cancelled at this stage.")

    return redirect("app:view_orders")

@login_required
def update_cart_quantity(request, item_id):
    if request.method == "POST":
        item = get_object_or_404(CartProduct, id=item_id)

        # Retrieve the product or variant associated with the cart item
        product = item.product
        variant = item.variant  # May be None if it's a base product
        quantity = int(request.POST.get('quantity'))

        # Validate the requested quantity against the stock
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
                        "message": "You can only add up to " + str(product.max_per_user) + " items to your cart.",
                    }
                )

        # Update the quantity and recalculate the total price
        item.quantity = quantity
        item.save()

        # You may want to return the updated total price or any other info
        return JsonResponse({'success': True, 'total_price': item.total_price})

    return JsonResponse({'error': 'Invalid request'}, status=400)

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

    return render(request, "app/product_detail.html", {"product": product, "form": form})


@login_required
def add_to_wishlist(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        product = get_object_or_404(Product, id=product_id)
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)

        # Check if product is already in wishlist
        if wishlist.products.filter(id=product_id).exists():
            return JsonResponse({'status': 'danger', 'message': 'Product is already in your wishlist.'})
        
        wishlist.products.add(product)
        return JsonResponse({'status': 'success', 'message': 'Product added to wishlist!'})

@login_required
def remove_from_wishlist(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        product = get_object_or_404(Product, id=product_id)
        wishlist = Wishlist.objects.get(user=request.user)
        wishlist.products.remove(product)
        return JsonResponse({'status': 'removed'})
    
@login_required
def wishlist(request):
    wishlist = Wishlist.objects.get(user=request.user)
    products = wishlist.products.all()

    return render(request, 'app/wishlist.html', {'wishlist': wishlist, 'products': products})
