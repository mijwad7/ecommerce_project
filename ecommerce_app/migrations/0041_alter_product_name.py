# Generated by Django 5.1 on 2024-11-13 13:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce_app', '0040_alter_brand_name_alter_category_name_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='name',
            field=models.CharField(max_length=30),
        ),
    ]