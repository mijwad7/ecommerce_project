from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from .models import CartProduct, Product, Order, OrderItem


@receiver(post_save, sender=OrderItem)
def adjust_stock_on_order(sender, instance, created, **kwargs):
    if created:
        # Reduce stock based on the quantity of the new CartProduct
        instance.product.stock -= instance.quantity
        instance.product.save()

@receiver(post_save, sender=Order)
def adjust_stock_on_order_status_change(sender, instance, **kwargs):
    if instance.order_status == 'CANCELLED':
        for item in instance.items.all():
            item.product.stock += item.quantity
            item.product.save()