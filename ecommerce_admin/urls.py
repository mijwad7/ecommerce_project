from django.urls import path

from . import views

urlpatterns = [
    path("", views.generate_sales_report, name="admin_dashboard"),
    path("login/", views.login_view, name="login"),
    path("demo_login/", views.demo_login, name="demo_login"),
    path("logout/", views.logout_view, name="logout"),
    path("users/", views.user_list, name="user_list"),
    path("users/create/", views.create_user, name="create_user"),
    path("users/edit/<int:user_id>/", views.edit_user, name="edit_user"),
    path("categories/", views.categories_list, name="categories_list"),
    path("categories/add/", views.add_category, name="add_category"),
    path(
        "categories/edit/<int:category_id>/", views.edit_category, name="edit_category"
    ),
    path(
        "categories/delete/<int:category_id>/",
        views.delete_category,
        name="delete_category",
    ),
    path("brands/", views.brands_list, name="brands_list"),
    path("brands/add/", views.add_brand, name="add_brand"),
    path("brands/edit/<int:brand_id>/", views.edit_brand, name="edit_brand"),
    path("brands/delete/<int:brand_id>/", views.delete_brand, name="delete_brand"),
    path("products/", views.products_list, name="products_list"),
    path("products/add/", views.add_product, name="add_product"),
    path("products/<int:product_id>/", views.product_detail, name="product_detail"),
    path("products/edit/<int:product_id>/", views.edit_product, name="edit_product"),
    path(
        "products/delete/<int:product_id>/", views.delete_product, name="delete_product"
    ),
    path(
        "view_deleted_products/",
        views.view_deleted_products,
        name="view_deleted_products",
    ),
    path(
        "restore_product/<int:product_id>/",
        views.restore_product,
        name="restore_product",
    ),
    path(
        "view_deleted_categories/",
        views.view_deleted_categories,
        name="view_deleted_categories",
    ),
    path("view_deleted_brands/", views.view_deleted_brands, name="view_deleted_brands"),
    path(
        "restore_category/<int:category_id>/",
        views.restore_category,
        name="restore_category",
    ),
    path(
        "add_product_variant/<int:product_id>/",
        views.add_product_variant,
        name="add_product_variant",
    ),
    path(
        "product_variant/<int:variant_id>/",
        views.product_variant_detail,
        name="product_variant_detail",
    ),
    path(
        "product/variant/<int:variant_id>/edit/",
        views.edit_product_variant,
        name="edit_product_variant",
    ),
    path(
        "product/variant/<int:variant_id>/delete/",
        views.delete_product_variant,
        name="delete_product_variant",
    ),
    path("orders/", views.view_orders, name="view_orders"),
    path(
        "change_order_status/<int:order_id>/",
        views.change_order_status,
        name="change_order_status",
    ),
    path("cancel_order/<int:order_id>/", views.cancel_order, name="cancel_order"),
    path("tags/", views.tags_list, name="tags_list"),
    path("tags/add/", views.add_tag, name="add_tag"),
    path("tags/edit/<int:tag_id>/", views.edit_tag, name="edit_tag"),
    path("tags/delete/<int:tag_id>/", views.delete_tag, name="delete_tag"),
    path("offers/coupons/", views.coupon_list, name="coupon_list"),
    path("coupons/add/", views.add_coupon, name="add_coupon"),
    path("coupons/<int:coupon_id>/edit/", views.edit_coupon, name="edit_coupon"),
    path("coupons/<int:coupon_id>/delete/", views.delete_coupon, name="delete_coupon"),
    path(
        "sales_report/pdf/",
        views.generate_sales_report_pdf,
        name="generate_sales_report_pdf",
    ),
    path(
        "sales_report/excel/",
        views.generate_sales_report_excel,
        name="generate_sales_report_excel",
    ),
    path("offers/", views.offers_list, name="offers_list"),
    path("offers/products/", views.product_offers_list, name="product_offers_list"),
    path("offers/categories/", views.category_offers_list, name="category_offers_list"),
    path("offers/categories/add/", views.add_category_offer, name="add_category_offer"),
    path(
        "offers/categories/edit/<int:offer_id>/",
        views.edit_category_offer,
        name="edit_category_offer",
    ),
    path(
        "offers/categories/delete/<int:offer_id>/",
        views.delete_category_offer,
        name="delete_category_offer",
    ),
    path("return-requests/", views.view_return_requests, name="view_return_requests"),
    path(
        "approve-request/<int:request_id>/",
        views.approve_request,
        name="approve_request",
    ),
    path(
        "reject-request/<int:request_id>/", views.reject_request, name="reject_request"
    ),
]
