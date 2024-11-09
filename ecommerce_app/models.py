from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta
from PIL import Image as PilImage
from django_otp.models import Device
from django.contrib.auth.models import User
import random
import os
from django.conf import settings
from phonenumber_field.modelfields import PhoneNumberField
from decimal import Decimal, ROUND_DOWN




class UserProfile(AbstractUser):
    email = models.EmailField(unique=True, null=True, blank=True)
    is_blocked = models.BooleanField(default=False)
    phone_number = PhoneNumberField(unique=True, null=True, blank=True)

    def __str__(self):
        return self.username


class Address(models.Model):
    ADDRESS_TYPES = [
        ('billing', 'Billing'),
        ('shipping', 'Shipping'),
        ('office', 'Office'),
        ('home', 'Home'),
    ]
    
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='addresses')
    line_1 = models.TextField()
    line_2 = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    post_code = models.CharField(max_length=6)
    is_primary = models.BooleanField(default=False)
    address_type = models.CharField(max_length=20, choices=ADDRESS_TYPES)

    def __str__(self):
        return f"{self.user.username} - {self.get_address_type_display()} - {self.line_1}"
    
    def save(self, *args, **kwargs):
        if self.is_primary:
            # Make sure no other addresses are marked as primary for this user
            Address.objects.filter(user=self.user, is_primary=True).update(is_primary=False)
        super(Address, self).save(*args, **kwargs)

class CategoryQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_deleted=False)

    def deleted(self):
        return self.filter(is_deleted=True)


class CategoryManager(models.Manager):
    def get_queryset(self):
        return CategoryQuerySet(self.model).active()

    def all_objects(self):
        return CategoryQuerySet(self.model)


class Category(models.Model):
    name = models.CharField(max_length=20)
    is_deleted = models.BooleanField(default=False)

    objects = CategoryManager()

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()

    def restore(self, *args, **kwargs):
        self.is_deleted = False
        self.save()

    def delete_with_warning(self):
        # Check if there are products in this category
        products = self.products.filter(is_deleted=False)

        # Proceed to soft delete the category
        self.is_deleted = True
        self.save()
        
        # Optionally, also delist the products if required
        products.update(is_deleted=True)

    def __str__(self):
        return self.name
    
class CategoryOffer(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='offers')
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        now = timezone.now()
        if self.start_date > now or self.end_date < now:
            self.is_active = False
        super().save(*args, **kwargs)
        self.apply_discount_to_products()

    def apply_discount_to_products(self):
        if self.is_active:
            for product in self.category.products.all():
                product.is_on_sale = True
                discount_multiplier = Decimal(1) - (Decimal(self.discount_percent) / Decimal(100))
                sale_price = product.price * discount_multiplier
                
                # Round sale_price to two decimal places
                product.sale_price = sale_price.quantize(Decimal('0.01'), rounding=ROUND_DOWN)
                product.save()
        else:
            for product in self.category.products.all():
                product.is_on_sale = False
                product.sale_price = None
                product.save()

    def __str__(self):
        return f"{self.category} - {self.discount_percent}%"


class BrandQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_deleted=False)

    def deleted(self):
        return self.filter(is_deleted=True)


class BrandManager(models.Manager):
    def get_queryset(self):
        return BrandQuerySet(self.model).active()

    def all_objects(self):
        return BrandQuerySet(self.model)


class Brand(models.Model):
    name = models.CharField(max_length=20)
    is_deleted = models.BooleanField(default=False)

    objects = BrandManager()

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()

    def restore(self, *args, **kwargs):
        self.is_deleted = False
        self.save()

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=20)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='tags')

    def __str__(self):
        return self.name

class ProductQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_deleted=False, category__is_deleted=False)

    def deleted(self):
        return self.filter(is_deleted=True)


class ProductManager(models.Manager):
    def get_queryset(self):
        return ProductQuerySet(self.model).active()

    def all_objects(self):
        return ProductQuerySet(self.model)


class Coupon(models.Model):
    code = models.CharField(max_length=20)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        now = timezone.now()
        if self.start_date > now or self.end_date < now:
            self.is_active = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} - {self.discount_percent}%"


class Product(models.Model):
    name = models.CharField(max_length=30)
    description = models.TextField()
    stock = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_on_sale = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    sale_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    brand = models.ForeignKey(
        Brand, on_delete=models.CASCADE, related_name="products", blank=True, null=True
    )
    is_deleted = models.BooleanField(default=False)
    coupons = models.ManyToManyField(Coupon, blank=True, related_name="products")
    max_per_user = models.PositiveIntegerField(default=10)
    tags = models.ManyToManyField(Tag, blank=True)

    objects = ProductManager()

    def __str__(self):
        return self.name

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()

    def restore(self, *args, **kwargs):
        self.is_deleted = False
        self.save()

    def clean(self):
        if self.is_on_sale and not self.sale_price:
            raise ValidationError("Sale price must be set if the product is on sale.")
        if self.is_on_sale and self.sale_price >= self.price:
            raise ValidationError("Sale price must be less than the regular price.")

        # if not self.images.exists() or self.images.count() < 3:
        #     raise ValidationError("Product must have at least 3 images.")

    def save(self, *args, **kwargs):
        self.full_clean()  # Calls the clean method before saving
        super().save(*args, **kwargs)


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to="product_images/")

    def save(self, *args, **kwargs):
        # Call the method to process the image before saving
        super().save(*args, **kwargs)
        self.process_image()

    def process_image(self):
        img = PilImage.open(self.image)
        img = img.convert("RGB")  # Convert to RGB if it's not

        # Resize the image to a maximum of 800x800 while keeping the aspect ratio
        img.thumbnail((500, 500), PilImage.LANCZOS)

        # Save the image back to the specified path
        img.save(self.image.path)


class ProductSpec(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="specs")
    key = models.CharField(max_length=50)
    value = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.key}: {self.value}"


class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="variants"
    )
    name = models.CharField(
        max_length=100, help_text="Variant name (e.g., iPhone 15 Pro, Blue)"
    )
    variant_type = models.CharField(
        max_length=50, help_text="Type of variant (e.g., model, color, size)"
    )
    value = models.CharField(
        max_length=50, help_text="Specific variant value (e.g., Blue, 128GB)"
    )
    stock = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_on_sale = models.BooleanField(default=False)
    sale_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["product", "variant_type", "value"], name="unique_variant"
            )
        ]

    def __str__(self):
        return f"{self.product.name} - {self.variant_type}: {self.value}"


class ProductVariantImage(models.Model):
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to="variant_images/")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.process_image()

    def process_image(self):
        img = PilImage.open(self.image)
        img = img.convert("RGB")

        # Resize the image to a maximum of 500x500 while maintaining the aspect ratio
        img.thumbnail((500, 500), PilImage.LANCZOS)

        img.save(self.image.path)


class EmailOTPDevice(Device):
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    otp_sent_at = models.DateTimeField(
        null=True, blank=True
    )  # Track when the OTP was sent

    OTP_EXPIRY_MINUTES = 2  # OTP will expire after 5 minutes

    def generate_otp(self):
        """Generate a 6-digit OTP code and set the timestamp."""
        self.otp_code = f"{random.randint(100000, 999999)}"
        self.otp_sent_at = timezone.now()
        self.save()
        return self.otp_code

    def verify_otp(self, otp):
        """Verify the given OTP."""
        # Check if OTP has expired
        if (
            self.otp_code
            and self.otp_sent_at
            and timezone.now()
            < self.otp_sent_at + timedelta(minutes=self.OTP_EXPIRY_MINUTES)
        ):
            if self.otp_code == otp:
                self.otp_code = None  # Clear OTP after successful verification
                self.otp_sent_at = None
                self.save()
                return True
        return False

    def is_otp_expired(self):
        """Check if the OTP has expired."""
        return (
            self.otp_sent_at is None
            or timezone.now()
            > self.otp_sent_at + timedelta(minutes=self.OTP_EXPIRY_MINUTES)
        )


class Review(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="reviews"
    )
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


class Cart(models.Model):
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name="cart")

    def __str__(self):
        return f"{self.user.username} - {self.total_price}"

    @property
    def total_price(self):
        return sum(item.total_price for item in self.cart_products.all())

    def total_items(self):
        return self.cart_products.count()


class CartProduct(models.Model):
    cart = models.ForeignKey(
        Cart, on_delete=models.CASCADE, related_name="cart_products"
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    variant = models.ForeignKey(ProductVariant, null=True, blank=True, on_delete=models.SET_NULL)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    is_checked_out = models.BooleanField(default=False)

    def __str__(self):
        variant_info = f" ({self.variant.value})" if self.variant else ""
        return f"{self.cart.user.username} - {self.product.name}{variant_info}"

    def clean(self):
        # Check stock availability
        available_stock = self.variant.stock if self.variant else self.product.stock
        if self.quantity > available_stock:
            raise ValidationError("Quantity cannot be greater than available stock.")

        # Check max quantity per user (assuming a field `max_per_user` in Product)
        if self.product.max_per_user and self.quantity > self.product.max_per_user:
            raise ValidationError(
                f"You can only add up to {self.product.max_per_user} of this product."
            )

    def save(self, *args, **kwargs):
        # Determine the price based on variant or base product
        if self.variant:
            price = (
                self.variant.sale_price if self.variant.is_on_sale else self.variant.price
            )
        else:
            price = (
                self.product.sale_price if self.product.is_on_sale else self.product.price
            )
        
        # Automatically set the total price based on the determined price and quantity
        self.total_price = price * self.quantity
        super().save(*args, **kwargs)


class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('COD', 'Cash on Delivery'),
        ('ONLINE', 'Online Payment'),
    ]
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='PENDING')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='COD')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    applied_coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    original_total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    wallet_deduction = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    address_line_1 = models.TextField()
    address_line_2 = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    post_code = models.CharField(max_length=6)

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

class Wishlist(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, related_name='wishlisted_by', blank=True)

    def __str__(self):
        return f"{self.user.username}'s Wishlist"


class Wallet(models.Model):
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name="wallet")
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    last_updated = models.DateTimeField(auto_now=True)

    def add_funds(self, amount):
        self.balance += amount
        self.save()

    def deduct_funds(self, amount):
        if amount <= self.balance:
            self.balance -= amount
            self.save()
            return True
        return False

    def __str__(self):
        return f"{self.user.username}'s Wallet - Balance: ₹{self.balance}"



class ProductReturnRequest(models.Model):
    RETURN_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    order_item = models.OneToOneField(OrderItem, on_delete=models.CASCADE, null=True, blank=True)
    reason = models.TextField()
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=RETURN_STATUS_CHOICES, default='PENDING')
    requested_at = models.DateTimeField(auto_now_add=True)
    message = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Return Request for {self.order_item.product.name} by {self.user.username}"