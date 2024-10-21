from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import CartProduct, Product

@receiver(post_save, sender=CartProduct)
def adjust_stock_on_add(sender, instance, created, **kwargs):
    """
    Adjust product stock when a CartProduct is created or updated.
    """
    if created:
        # Reduce stock when a new CartProduct is added
        instance.product.stock -= instance.quantity
    else:
        # Adjust stock based on quantity change if CartProduct is updated
        original = CartProduct.objects.get(pk=instance.pk)
        difference = instance.quantity - original.quantity
        instance.product.stock -= difference
    
    instance.product.save()

@receiver(post_delete, sender=CartProduct)
def adjust_stock_on_remove(sender, instance, **kwargs):
    """
    Restore product stock when a CartProduct is removed.
    """
    instance.product.stock += instance.quantity
    instance.product.save()
