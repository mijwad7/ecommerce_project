# Generated by Django 5.1 on 2024-10-15 07:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ecommerce_app", "0005_emailotpdevice"),
    ]

    operations = [
        migrations.AddField(
            model_name="emailotpdevice",
            name="otp_sent_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
