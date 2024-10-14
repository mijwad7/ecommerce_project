from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from PIL import Image as PilImage
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


class Product(models.Model):
    name = models.CharField(max_length=30)
    description = models.TextField()
    stock = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_on_sale = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    is_deleted = models.BooleanField(default=False)

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
        if self.is_on_sale and self.sale_price >= self.price:
            raise ValidationError("Sale price must be less than the regular price.")
        
        # if not self.images.exists() or self.images.count() < 3:
        #     raise ValidationError("Product must have at least 3 images.")


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
        img.thumbnail((800, 800), PilImage.LANCZOS)

        # Save the image back to the specified path
        img.save(self.image.path)