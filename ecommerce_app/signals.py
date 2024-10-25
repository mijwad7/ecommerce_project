from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from .models import CartProduct, Product

@receiver(pre_save, sender=CartProduct)
def adjust_stock_on_update(sender, instance, **kwargs):
    """
    Adjust product stock when a CartProduct is updated.
    """
    if instance.pk:
        # If the CartProduct already exists, get the original object
        original = CartProduct.objects.get(pk=instance.pk)
        if instance.quantity != original.quantity:
            # Calculate the difference and adjust stock accordingly
            difference = instance.quantity - original.quantity
            instance.product.stock -= difference
            instance.product.save()

@receiver(post_save, sender=CartProduct)
def adjust_stock_on_add(sender, instance, created, **kwargs):
    """
    Reduce product stock when a new CartProduct is added.
    """
    if created:
        # Reduce stock based on the quantity of the new CartProduct
        instance.product.stock -= instance.quantity
        instance.product.save()

@receiver(post_delete, sender=CartProduct)
def adjust_stock_on_remove(sender, instance, **kwargs):
    """
    Restore product stock when a CartProduct is removed.
    """
    if not instance.is_checked_out:
        instance.product.stock += instance.quantity
        instance.product.save()
