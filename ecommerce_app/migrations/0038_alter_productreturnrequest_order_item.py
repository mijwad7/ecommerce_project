# Generated by Django 5.1 on 2024-11-09 13:54

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ecommerce_app", "0037_alter_productreturnrequest_order_item"),
    ]

    operations = [
        migrations.AlterField(
            model_name="productreturnrequest",
            name="order_item",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="ecommerce_app.orderitem",
            ),
        ),
    ]
