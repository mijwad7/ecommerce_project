# Generated by Django 5.1 on 2024-11-02 13:11

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ecommerce_app", "0029_wallet"),
    ]

    operations = [
        migrations.CreateModel(
            name="CategoryOffer",
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
                (
                    "discount_percent",
                    models.DecimalField(decimal_places=2, max_digits=5),
                ),
                ("start_date", models.DateTimeField()),
                ("end_date", models.DateTimeField()),
                ("is_active", models.BooleanField(default=True)),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="offers",
                        to="ecommerce_app.category",
                    ),
                ),
            ],
        ),
    ]
