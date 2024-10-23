from django.urls import path, include
from . import views

app_name = 'app'

urlpatterns = [
    path('', views.index, name='index'),
    path('signup/', views.user_signup, name='user_signup'),
    path('login/', views.user_login, name='user_login'),
    path('demo_login/', views.demo_login, name='demo_login'),
    path('logout/', views.user_logout, name='user_logout'),
    path('products/', views.products, name='products'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('products/<int:product_id>/', views.product_detail, name='product_detail'),
    path('get-variant-details/<int:variant_id>/', views.get_variant_details, name='get_variant_details'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.view_cart, name='view_cart'),
    path('remove-from-cart/<int:cartproduct_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('add-address/', views.add_address, name='add_address'),
    path('edit-address/<int:address_id>/', views.edit_address, name='edit_address'),
    path('delete-address/<int:address_id>/', views.delete_address, name='delete_address'),
    path('profile/', views.view_profile, name='view_profile'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('change-password/', views.change_password, name='change_password'),
    
]
