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


class UserProfile(AbstractUser):
    email = models.EmailField(unique=True, null=True, blank=True)
    is_blocked = models.BooleanField(default=False)

    def __str__(self):
        return self.username


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

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_deleted=False)

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
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    is_deleted = models.BooleanField(default=False)
    coupons = models.ManyToManyField(Coupon, blank=True, related_name="products")

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
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='specs')
    key = models.CharField(max_length=50)
    value = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.key}: {self.value}"


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
