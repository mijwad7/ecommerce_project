from django.apps import AppConfig


class EcommerceAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ecommerce_app'

    def ready(self):
        from . import signals
