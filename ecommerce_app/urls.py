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
    path('products/<int:product_id>/', views.product_detail, name='product_detail')
]
