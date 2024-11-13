from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from .models import CartProduct, Product, Order, OrderItem, ProductReturnRequest


@receiver(post_save, sender=OrderItem)
def adjust_stock_on_order(sender, instance, created, **kwargs):
    if created:
        # Reduce stock based on the quantity of the new CartProduct
        instance.product.stock -= instance.quantity
        instance.product.save()


@receiver(post_save, sender=Order)
def adjust_stock_on_order_status_change(sender, instance, **kwargs):
    if instance.order_status == "CANCELLED":
        for item in instance.items.all():
            item.product.stock += item.quantity
            item.product.save()


@receiver(post_save, sender=ProductReturnRequest)
def update_stock_on_return_request(sender, instance, **kwargs):
    # Increase stock based on the quantity of the returned ProductReturnRequest
    if instance.status == "APPROVED":
        instance.order_item.product.stock += instance.order_item.quantity
        instance.order_item.product.save()
