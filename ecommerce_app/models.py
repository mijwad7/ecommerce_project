from django.db import models
from django.contrib.auth.models import AbstractUser


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
