# Generated by Django 5.1 on 2024-11-09 13:49

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ecommerce_app", "0036_productreturnrequest_message"),
    ]

    operations = [
        migrations.AlterField(
            model_name="productreturnrequest",
            name="order_item",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="ecommerce_app.orderitem",
                unique=True,
            ),
        ),
    ]
