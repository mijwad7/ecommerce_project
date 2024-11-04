# Generated by Django 5.1 on 2024-11-03 17:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce_app', '0032'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='address',
        ),
        migrations.AlterField(
            model_name='order',
            name='address_line_1',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='order',
            name='city',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='order',
            name='post_code',
            field=models.CharField(max_length=6),
        ),
        migrations.AlterField(
            model_name='order',
            name='state',
            field=models.CharField(max_length=50),
        ),
    ]