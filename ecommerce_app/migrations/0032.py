from django.db import migrations


def copy_address_data(apps, schema_editor):
    Order = apps.get_model("ecommerce_app", "Order")
    Address = apps.get_model("ecommerce_app", "Address")

    for order in Order.objects.all():
        # Assuming each order has an associated address
        if order.address:
            order.address_line_1 = order.address.line_1
            order.address_line_2 = order.address.line_2
            order.city = order.address.city
            order.state = order.address.state
            order.post_code = order.address.post_code
            order.save()


class Migration(migrations.Migration):
    dependencies = [
        (
            "ecommerce_app",
            "0031_order_address_line_1_order_address_line_2_order_city_and_more",
        ),
    ]

    operations = [
        migrations.RunPython(copy_address_data),
    ]
