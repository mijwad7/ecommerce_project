# Generated by Django 5.1 on 2024-10-18 12:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("ecommerce_app", "0012_category_parent"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="category",
            name="parent",
        ),
    ]
