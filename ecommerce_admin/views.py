from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from ecommerce_app.models import (
    UserProfile,
    Category,
    Product,
    ProductImage,
    ProductSpec,
    Brand,
    ProductVariantImage,
    ProductVariant,
    Order,
    Tag,
    Coupon,
    CategoryOffer,
    ProductReturnRequest
)
from .forms import (
    UserProfileForm,
    LoginForm,
    ProductForm,
    ProductSpecFormSet,
    ProductVariantForm,
    CouponForm,
    CategoryOfferForm
)
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.db.models import Q, Sum, Count, F, Value, DecimalField, Case, When
from django.utils import timezone
from datetime import timedelta, datetime
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
from openpyxl import Workbook
import plotly.express as px
import json
import plotly

def superuser_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        return HttpResponseForbidden("You do not have permission to access this page.")

    return _wrapped_view


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("admin_dashboard")
            else:
                form.add_error(None, "Invalid credentials")
    else:
        form = LoginForm()
    return render(request, "admin/login.html", {"form": form})


@login_required
def logout_view(request):
    logout(request)
    return redirect("login")


def demo_login(request):
    user = authenticate(username="mijwad", password="1234")
    if user is not None:
        login(request, user)
        return redirect("admin_dashboard")  # Redirect to the main page after login
    else:
        # Handle case where demo user is not set up properly
        return redirect("login")




@login_required
@superuser_required
def user_list(request):
    users = UserProfile.objects.all()
    return render(request, "admin/user_list.html", {"users": users})


@login_required
@superuser_required
def create_user(request):
    if request.method == "POST":
        form = UserProfileForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("user_list")
    else:
        form = UserProfileForm()
    return render(request, "admin/create_user.html", {"form": form})


@login_required
@superuser_required
def edit_user(request, user_id):
    user = get_object_or_404(UserProfile, id=user_id)
    if request.method == "POST":
        user.email = request.POST.get("email", user.email)
        user.is_blocked = "is_blocked" in request.POST
        user.is_superuser = "is_superuser" in request.POST
        user.is_active = "is_active" in request.POST
        user.save()
        return redirect("user_list")
    return render(request, "admin/edit_user.html", {"user": user})


@login_required
@superuser_required
def categories_list(request):
    categories = Category.objects.all()
    return render(request, "admin/categories_list.html", {"categories": categories})


@login_required
@superuser_required
def add_category(request):
    if request.method == "POST":
        category_name = request.POST.get("category_name")
        if category_name:
            Category.objects.create(name=category_name)
            messages.success(request, "Category added successfully!")
            return redirect("categories_list")
        else:
            messages.error(request, "Please enter a category name.")
    return render(request, "admin/add_category.html")


@login_required
@superuser_required
def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == "POST":
        category_name = request.POST.get("name")
        if category_name:
            category.name = category_name
            category.save()
            messages.success(request, "Category updated successfully!")
            return redirect("categories_list")
        else:
            messages.error(request, "Please enter a category name.")
    return render(request, "admin/edit_category.html", {"category": category})


@login_required
@superuser_required
def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == "POST":
        try:
            category.delete_with_warning()
            messages.success(request, "Category deleted successfully.")
        except ValueError as e:
            messages.error(request, str(e))
        return redirect("categories_list")
    return render(request, "admin/delete_category.html", {"category": category})


@login_required
@superuser_required
def brands_list(request):
    brands = Brand.objects.all()
    return render(request, "admin/brands_list.html", {"brands": brands})


@login_required
@superuser_required
def add_brand(request):
    if request.method == "POST":
        brand_name = request.POST.get("brand_name")
        if brand_name:
            Brand.objects.create(name=brand_name)
            messages.success(request, "Brand added successfully!")
            return redirect("brands_list")
        else:
            messages.error(request, "Please enter a brand name.")
    return render(request, "admin/add_brand.html")


@login_required
@superuser_required
def edit_brand(request, brand_id):
    brand = get_object_or_404(Brand, id=brand_id)
    if request.method == "POST":
        brand_name = request.POST.get("name")
        if brand_name:
            brand.name = brand_name
            brand.save()
            messages.success(request, "Brand updated successfully!")
            return redirect("brands_list")
        else:
            messages.error(request, "Please enter a brand name.")
    return render(request, "admin/edit_brand.html", {"brand": brand})


@login_required
@superuser_required
def delete_brand(request, brand_id):
    brand = get_object_or_404(Brand, id=brand_id)
    if request.method == "POST":
        brand.delete()
        messages.success(request, "Brand deleted successfully!")
        return redirect("brands_list")
    return render(request, "admin/delete_brand.html", {"brand": brand})


@login_required
@superuser_required
def products_list(request):
    query = request.GET.get("query")
    category_id = request.GET.get("category")
    sort_by = request.GET.get("sort", "id")
    products = Product.objects.all()

    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    if category_id:
        products = products.filter(category_id=category_id)

    if sort_by == "name":
        products = products.order_by("name")
    elif sort_by == "price":
        products = products.order_by("price")
    elif sort_by == "category":
        products = products.order_by("category__name")
    else:
        products = products.order_by("-id")

    return render(
        request,
        "admin/products_list.html",
        {
            "products": products,
            "categories": Category.objects.all(),
        },
    )


@login_required
@superuser_required
def add_product(request):
    if request.method == "POST":
        product_form = ProductForm(request.POST, request.FILES)
        formset = ProductSpecFormSet(request.POST, instance=product_form.instance)

        if product_form.is_valid() and formset.is_valid():
            product = product_form.save()

            # Collect the uploaded images
            uploaded_images = request.FILES.getlist("images")

            # Check if there are at least 3 images
            if len(uploaded_images) < 3:
                product.delete()  # Remove the product if not enough images
                messages.error(request, "You must upload at least 3 images.")
                return render(
                    request,
                    "admin/add_product.html",
                    {"product_form": product_form, "formset": formset},
                )

            # Save the images after validation
            for image in uploaded_images:
                ProductImage.objects.create(product=product, image=image)

            # Save the specifications
            formset.save()

            messages.success(request, "Product added successfully!")
            return redirect("products_list")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        product_form = ProductForm()
        formset = ProductSpecFormSet()

    return render(
        request,
        "admin/add_product.html",
        {"product_form": product_form, "formset": formset},
    )


@login_required
@superuser_required
def product_detail(request, product_id):
    product = get_object_or_404(Product.objects.all_objects(), id=product_id)
    specs = ProductSpec.objects.filter(product=product)
    variants = ProductVariant.objects.filter(product=product)
    return render(
        request,
        "admin/product_detail.html",
        {"product": product, "specs": specs, "variants": variants},
    )


@login_required
@superuser_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == "POST":
        product.delete()
        messages.success(request, "Product deleted successfully!")
        return redirect("products_list")
    return render(request, "admin/delete_product.html", {"product": product})


@login_required
@superuser_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == "POST":
        product_form = ProductForm(request.POST, request.FILES, instance=product)

        if product_form.is_valid():
            product = product_form.save()
            uploaded_images = request.FILES.getlist("images")

            if uploaded_images:
                for image in uploaded_images:
                    ProductImage.objects.create(product=product, image=image)

            messages.success(request, "Product updated successfully!")
            return redirect("product_detail", product_id=product.id)

        else:
            messages.error(request, "Please correct the errors below.")

    else:
        product_form = ProductForm(instance=product)

    return render(
        request,
        "admin/edit_product.html",
        {"product_form": product_form, "product": product},
    )


@login_required
@superuser_required
def add_product_variant(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        variant_form = ProductVariantForm(request.POST)
        uploaded_images = request.FILES.getlist("images")

        if variant_form.is_valid():
            variant = variant_form.save(commit=False)
            variant.product = product

            # Ensure at least 3 images are provided
            if len(uploaded_images) < 3:
                messages.error(request, "Each variant must have at least 3 images.")
                return render(
                    request,
                    "admin/add_product_variant.html",
                    {"variant_form": variant_form},
                )

            variant.save()

            # Save variant images
            for image in uploaded_images:
                ProductVariantImage.objects.create(variant=variant, image=image)

            messages.success(request, "Product variant added successfully!")
            return redirect("product_detail", product_id=product.id)

        else:
            messages.error(request, "Please correct the errors below.")

    else:
        variant_form = ProductVariantForm()

    return render(
        request,
        "admin/add_product_variant.html",
        {
            "variant_form": variant_form,
            "product": product,
        },
    )


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
        "variant": variant,
        "images": variant.images.all(),
    }
    return render(request, "admin/variant_detail.html", context)


@login_required
@superuser_required
def edit_product_variant(request, variant_id):
    variant = get_object_or_404(ProductVariant, id=variant_id)
    product = variant.product  # Get the parent product

    if request.method == "POST":
        variant_form = ProductVariantForm(request.POST, instance=variant)
        uploaded_images = request.FILES.getlist("images")

        if variant_form.is_valid():
            variant = variant_form.save()

            # If new images are uploaded, delete the old ones and save the new ones
            if uploaded_images:
                ProductVariantImage.objects.filter(
                    variant=variant
                ).delete()  # Delete existing images
                for image in uploaded_images:
                    ProductVariantImage.objects.create(variant=variant, image=image)

            messages.success(request, "Product variant updated successfully!")
            return redirect("product_variant_detail", variant_id=variant.id)

        else:
            messages.error(request, "Please correct the errors below.")

    else:
        variant_form = ProductVariantForm(instance=variant)

    return render(
        request,
        "admin/edit_product_variant.html",
        {
            "variant_form": variant_form,
            "product": product,
            "variant": variant,
        },
    )


@login_required
@superuser_required
def delete_product_variant(request, variant_id):
    variant = get_object_or_404(ProductVariant, id=variant_id)
    product = variant.product  # Get the parent product

    if request.method == "POST":
        variant.delete()
        messages.success(request, "Product variant deleted successfully!")
        return redirect("product_detail", product_id=product.id)

    return render(
        request,
        "admin/delete_product_variant.html",
        {"variant": variant, "product": product},
    )


@login_required
@superuser_required
def view_deleted_products(request):
    products = Product.objects.all_objects().deleted()
    return render(request, "admin/view_deleted_products.html", {"products": products})


@login_required
@superuser_required
def restore_product(request, product_id):
    product = get_object_or_404(Product.objects.all_objects(), id=product_id)
    if request.method == "POST":
        product.restore()
        product.save()
        messages.success(request, "Product restored successfully!")
        return redirect("products_list")
    return render(request, "admin/view_deleted_products.html", {"product": product})


@login_required
@superuser_required
def view_deleted_categories(request):
    categories = Category.objects.all_objects().deleted()
    return render(
        request, "admin/view_deleted_categories.html", {"categories": categories}
    )


@login_required
@superuser_required
def restore_category(request, category_id):
    category = get_object_or_404(Category.objects.all_objects(), id=category_id)
    if request.method == "POST":
        category.restore()
        category.save()
        messages.success(request, "Category restored successfully!")
        return redirect("categories_list")
    return render(request, "admin/view_deleted_categories.html", {"category": category})


@login_required
@superuser_required
def view_deleted_brands(request):
    brands = Brand.objects.all_objects().deleted()
    return render(request, "admin/view_deleted_brands.html", {"brands": brands})


@login_required
@superuser_required
def restore_brand(request, brand_id):
    brand = get_object_or_404(Brand.objects.all_objects(), id=brand_id)
    if request.method == "POST":
        brand.restore()
        brand.save()
        messages.success(request, "Brand restored successfully!")
        return redirect("brands_list")
    return render(request, "admin/view_deleted_brands.html", {"brand": brand})


@login_required
@superuser_required
def view_orders(request):
    orders = Order.objects.all().order_by("-id")
    return render(request, "admin/view_orders.html", {"orders": orders})


@login_required
@superuser_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)  # Remove user restriction
    if order.order_status in ["PENDING", "CONFIRMED"]:
        order.order_status = "CANCELLED"
        order.save()
        messages.success(request, "Order canceled successfully!")
    else:
        messages.error(request, "Order cannot be cancelled at this stage.")
    return redirect("view_orders")


@login_required
@superuser_required
def change_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)  # Remove user restriction
    new_status = request.POST.get(
        "status"
    )  # Ensure you retrieve the correct field name
    if new_status in dict(Order.ORDER_STATUS_CHOICES):  # Validate against choices
        order.order_status = new_status
        order.save()
        messages.success(request, "Order status changed successfully!")
    else:
        messages.error(request, "Invalid status selected.")
    return redirect("view_orders")


@login_required
@superuser_required
def tags_list(request):
    tags = Tag.objects.all()
    return render(request, "admin/tags_list.html", {"tags": tags})


@login_required
@superuser_required
def add_tag(request):
    categories = Category.objects.all()
    if request.method == "POST":
        tag_name = request.POST.get("tag_name")
        category_id = request.POST.get("category")
        category = Category.objects.filter(id=category_id).first()

        if tag_name and category:
            Tag.objects.create(name=tag_name, category=category)
            messages.success(request, "Tag added successfully!")
            return redirect("tags_list")
        else:
            messages.error(request, "Please enter a tag name and select a category.")
    return render(request, "admin/add_tag.html", {"categories": categories})


@login_required
@superuser_required
def edit_tag(request, tag_id):
    tag = get_object_or_404(Tag, id=tag_id)
    categories = Category.objects.all()
    if request.method == "POST":
        tag_name = request.POST.get("name")
        category_id = request.POST.get("category")
        category = Category.objects.filter(id=category_id).first()

        if tag_name and category:
            tag.name = tag_name
            tag.category = category
            tag.save()
            messages.success(request, "Tag updated successfully!")
            return redirect("tags_list")
        else:
            messages.error(request, "Please enter a tag name and select a category.")
    return render(
        request, "admin/edit_tag.html", {"tag": tag, "categories": categories}
    )


@login_required
@superuser_required
def delete_tag(request, tag_id):
    tag = get_object_or_404(Tag, id=tag_id)
    if request.method == "POST":
        tag.delete()
        messages.success(request, "Tag deleted successfully!")
        return redirect("tags_list")
    return render(request, "admin/delete_tag.html", {"tag": tag})


@login_required
@superuser_required
def coupon_list(request):
    coupons = Coupon.objects.all()
    return render(request, 'admin/coupons_list.html', {'coupons': coupons})

@login_required
@superuser_required
def add_coupon(request):
    if request.method == 'POST':
        form = CouponForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Coupon added successfully!")
            return redirect('coupon_list')
        else:
            messages.error(request, "There was an error adding the coupon.")
    else:
        form = CouponForm()
    return render(request, 'admin/add_coupon.html', {'form': form})

@login_required
@superuser_required
def edit_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    if request.method == 'POST':
        form = CouponForm(request.POST, instance=coupon)
        if form.is_valid():
            form.save()
            messages.success(request, "Coupon updated successfully!")
            return redirect('coupon_list')
        else:
            messages.error(request, "There was an error updating the coupon.")
    else:
        form = CouponForm(instance=coupon)
    return render(request, 'admin/add_coupon.html', {'form': form})

@login_required
@superuser_required
def delete_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    coupon.delete()
    messages.success(request, "Coupon deleted successfully.")
    return redirect('coupon_list')



def calculate_date_range(date_filter):
    today = timezone.now()

    if date_filter == 'daily':
        start_date = today - timedelta(days=1)
    elif date_filter == 'weekly':
        start_date = today - timedelta(weeks=1)
    elif date_filter == 'monthly':
        start_date = today - timedelta(days=30)
    elif date_filter == 'yearly':
        start_date = today - timedelta(days=365)
    else:
        # Custom range; if date_filter is custom or invalid, use a default range
        start_date = today - timedelta(days=7)

    end_date = today
    return start_date, end_date


@login_required
@superuser_required
def generate_sales_report(request):
    filter_type = request.GET.get('filter_type', 'predefined')
    date_filter = request.GET.get('date_filter', 'weekly')  # Default to weekly
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if filter_type == 'custom' and date_from and date_to:
        start_date = datetime.strptime(date_from, '%Y-%m-%d').date()
        end_date = datetime.strptime(date_to, '%Y-%m-%d').date()
    else:
        start_date, end_date = calculate_date_range(date_filter)

    # Query filtered orders
    orders = Order.objects.filter(
        created_at__range=(start_date, end_date),
    ).exclude(
        order_status='CANCELLED'
    ).annotate(
        discount_amount=Case(
            When(original_total_price__isnull=False,
                 then=F('original_total_price') - F('total_price')),
            default=Value(0),
            output_field=DecimalField()
        )
    ).order_by('-created_at')

    # Aggregate data for the report
    discounted_orders = orders.filter(original_total_price__isnull=False)
    total_discount = discounted_orders.aggregate(
        total_discount=Sum('original_total_price') - Sum('total_price')
    )['total_discount'] or 0

    dates = [order.created_at.strftime('%Y-%m-%d') for order in orders]
    sales_data = [order.total_price for order in orders]

    fig = px.line(x=dates, y=sales_data, labels={'x': 'Date', 'y': 'Total Sales'},
                  title="Sales Report")
    fig_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return render(request, "admin/index.html", {
        "total_sales": orders.aggregate(total_sales=Sum('total_price'))['total_sales'] or 0,
        "total_orders": orders.count(),
        "total_discount": total_discount,
        "orders": orders,
        "start_date": start_date,
        "end_date": end_date,
        "date_filter": date_filter,
        'plotly_fig': fig_json,
    })



@login_required
@superuser_required
def generate_sales_report_pdf(request):
    filter_type = request.GET.get('filter_type', 'predefined')
    date_filter = request.GET.get('date_filter', 'weekly')  # Default to weekly
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if filter_type == 'custom' and date_from and date_to:
        start_date = datetime.strptime(date_from, '%Y-%m-%d').date()
        end_date = datetime.strptime(date_to, '%Y-%m-%d').date()
    else:
        start_date, end_date = calculate_date_range(date_filter)

    display_start_date = start_date.strftime('%Y-%m-%d')
    display_end_date = end_date.strftime('%Y-%m-%d')

    # Query filtered orders
    orders = Order.objects.filter(
        created_at__range=(start_date, end_date),
    ).exclude(
        order_status='CANCELLED'
    ).annotate(
        discount_amount=Case(
            When(original_total_price__isnull=False,
                 then=F('original_total_price') - F('total_price')),
            default=Value(0),
            output_field=DecimalField()
        )
    ).order_by('-created_at')

    # Aggregate data for the report
    total_discount = orders.filter(original_total_price__isnull=False).aggregate(
        total_discount=Sum('original_total_price') - Sum('total_price')
    )['total_discount'] or 0

    # Create the PDF response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="sales_report.pdf"'

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Draw PDF content
    p.drawString(100, height - 50, "Sales Report")
    p.drawString(100, height - 80, f"Date Range: {display_start_date} to {display_end_date}")
    p.drawString(100, height - 100, f"Total Orders: {orders.count()}")
    p.drawString(100, height - 120, f"Total Sales Amount: {orders.aggregate(total_sales=Sum('total_price'))['total_sales'] or 0:.2f}")
    p.drawString(100, height - 140, f"Total Discount Given: {total_discount:.2f}")

    # Add table headers
    p.drawString(100, height - 180, "Order ID")
    p.drawString(150, height - 180, "Order Date")
    p.drawString(300, height - 180, "Made by")
    p.drawString(400, height - 180, "Total Amount")
    p.drawString(500, height - 180, "Discount")

    # Draw table rows
    y_position = height - 200
    for order in orders:
        p.drawString(100, y_position, str(order.id))
        p.drawString(150, y_position, order.created_at.strftime("%Y-%m-%d %H:%M:%S"))
        p.drawString(300, y_position, order.user.username)
        p.drawString(400, y_position, f"{order.total_price:.2f}")
        p.drawString(500, y_position, f"{order.discount_amount:.2f}")
        y_position -= 20  # Move down for the next row

    p.showPage()
    p.save()
    buffer.seek(0)
    response.write(buffer.read())
    return response




@login_required
@superuser_required
def generate_sales_report_excel(request):
    filter_type = request.GET.get('filter_type', 'predefined')
    date_filter = request.GET.get('date_filter', 'weekly')  # Default to weekly
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if filter_type == 'custom' and date_from and date_to:
        start_date = datetime.strptime(date_from, '%Y-%m-%d').date()
        end_date = datetime.strptime(date_to, '%Y-%m-%d').date()
    else:
        start_date, end_date = calculate_date_range(date_filter)

    # Query filtered orders
    orders = Order.objects.filter(
        created_at__range=(start_date, end_date),
    ).exclude(
        order_status='CANCELLED'
    ).annotate(
        discount_amount=Case(
            When(original_total_price__isnull=False,
                 then=F('original_total_price') - F('total_price')),
            default=Value(0),
            output_field=DecimalField()
        )
    ).order_by('-created_at')

    # Create an Excel workbook and add a worksheet
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Sales Report"

    # Add headers to the Excel sheet
    headers = ["Order ID", "Order Date", "Made by", "Total Amount", "Discount"]
    sheet.append(headers)

    # Add data rows to the Excel sheet
    for order in orders:
        sheet.append([
            order.id,
            order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            order.user.username,
            order.total_price,
            order.discount_amount
        ])

    # Create the response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="sales_report.xlsx"'

    # Save the workbook to the response
    workbook.save(response)
    return response

@login_required
@superuser_required
def offers_list(request):
    products = Product.objects.filter(is_on_sale=True)
    return render(request, "admin/product_offers_list.html", {"products": products})

@login_required
@superuser_required
def product_offers_list(request):
    products = Product.objects.filter(is_on_sale=True)
    return render(request, "admin/product_offers_list.html", {"products": products})

@login_required
@superuser_required
def category_offers_list(request):
    category_offers = CategoryOffer.objects.all()
    return render(request, "admin/category_offers_list.html", {"category_offers": category_offers})

@login_required
@superuser_required
def add_category_offer(request):
    if request.method == 'POST':
        form = CategoryOfferForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Category Offer added successfully!")
            return redirect('category_offers_list')
        else:
            messages.error(request, "There was an error adding the category offer.")
    else:
        form = CategoryOfferForm()
    return render(request, 'admin/add_category_offer.html', {'form': form})

@login_required
@superuser_required
def edit_category_offer(request, offer_id):
    category_offer = get_object_or_404(CategoryOffer, id=offer_id)
    if request.method == 'POST':
        form = CategoryOfferForm(request.POST, instance=category_offer)
        if form.is_valid():
            form.save()
            messages.success(request, "Category Offer updated successfully!")
            return redirect('category_offers_list')
        else:
            messages.error(request, "There was an error updating the category offer.")
    else:
        form = CategoryOfferForm(instance=category_offer)
    return render(request, 'admin/add_category_offer.html', {'form': form})

@login_required
@superuser_required
def delete_category_offer(request, offer_id):
    category_offer = get_object_or_404(CategoryOffer, id=offer_id)
    category_offer.delete()
    messages.success(request, "Category Offer deleted successfully.")
    return redirect('category_offers_list')

def view_return_requests(request):
    return_requests = ProductReturnRequest.objects.all()
    return render(request, "admin/view_return_requests.html", {
        "return_requests": return_requests
    })

def approve_request(request, request_id):
    return_request = get_object_or_404(ProductReturnRequest, id=request_id)
    return_request.status = 'APPROVED'
    return_request.save()
    messages.success(request, "Request approved successfully.")
    return redirect('view_return_requests')