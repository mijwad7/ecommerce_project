from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='admin_dashboard'),
    path('login/', views.login_view, name='login'),
    path('demo_login/', views.demo_login, name='demo_login'),
    path('logout/', views.logout_view, name='logout'),
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.create_user, name='create_user'),
    path('users/edit/<int:user_id>/', views.edit_user, name='edit_user'),
    path('categories/', views.categories_list, name='categories_list'),
    path('categories/add/', views.add_category, name='add_category'),
    path('categories/edit/<int:category_id>/', views.edit_category, name='edit_category'),
    path('categories/delete/<int:category_id>/', views.delete_category, name='delete_category'),
    path('products/', views.products_list, name='products_list'),
    path('products/add/', views.add_product, name='add_product'),
    path('products/<int:product_id>/', views.product_detail, name='product_detail'),
    path('products/edit/<int:product_id>/', views.edit_product, name='edit_product'),
    path('products/delete/<int:product_id>/', views.delete_product, name='delete_product'),
]
