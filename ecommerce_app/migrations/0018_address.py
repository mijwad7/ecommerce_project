# Generated by Django 5.1 on 2024-10-22 19:05

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ecommerce_app", "0017_cartproduct_variant"),
    ]

    operations = [
        migrations.CreateModel(
            name="Address",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("line_1", models.TextField()),
                ("line_2", models.TextField(blank=True, null=True)),
                ("city", models.CharField(max_length=50)),
                ("state", models.CharField(max_length=50)),
                ("post_code", models.CharField(max_length=6)),
                ("is_primary", models.BooleanField(default=False)),
                (
                    "address_type",
                    models.CharField(
                        choices=[
                            ("billing", "Billing"),
                            ("shipping", "Shipping"),
                            ("office", "Office"),
                            ("home", "Home"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="addresses",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
