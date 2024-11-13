from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.urls import reverse_lazy


app_name = "app"

urlpatterns = [
    path("", views.index, name="index"),
    path("signup/", views.user_signup, name="user_signup"),
    path("login/", views.user_login, name="user_login"),
    path("demo_login/", views.demo_login, name="demo_login"),
    path("logout/", views.user_logout, name="user_logout"),
    path("products/", views.products, name="products"),
    path("verify-otp/", views.verify_otp, name="verify_otp"),
    path("privacy-policy/", views.privacy_policy, name="privacy_policy"),
    path("terms-of-service/", views.terms_of_service, name="terms_of_service"),
    path("products/<int:product_id>/", views.product_detail, name="product_detail"),
    path(
        "get-variant-details/<int:variant_id>/",
        views.get_variant_details,
        name="get_variant_details",
    ),
    path("add-to-cart/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("cart/", views.view_cart, name="view_cart"),
    path(
        "remove-from-cart/<int:cartproduct_id>/",
        views.remove_from_cart,
        name="remove_from_cart",
    ),
    path("add-address/", views.add_address, name="add_address"),
    path("edit-address/<int:address_id>/", views.edit_address, name="edit_address"),
    path(
        "delete-address/<int:address_id>/", views.delete_address, name="delete_address"
    ),
    path("profile/", views.view_profile, name="view_profile"),
    path("edit-profile/", views.edit_profile, name="edit_profile"),
    path("change-password/", views.change_password, name="change_password"),
    path(
        "password_reset/",
        auth_views.PasswordResetView.as_view(
            template_name="app/password_reset_form.html",
            email_template_name="app/password_reset_email.html",
            success_url="done/",
            extra_context={"app_name": app_name},
        ),
        name="password_reset",
    ),
    path(
        "password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="app/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="app/password_reset_confirm.html",
            success_url=reverse_lazy(
                "app:password_reset_complete"
            ),  # Use reverse_lazy here
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="app/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    path("checkout/", views.checkout, name="checkout"),
    path(
        "order-confirmation/<int:order_id>/",
        views.order_confirmation,
        name="order_confirmation",
    ),
    path("orders/", views.view_orders, name="view_orders"),
    path("order/<int:order_id>/", views.order_detail, name="order_detail"),
    path("cancel-order/<int:order_id>/", views.cancel_order, name="cancel_order"),
    path(
        "cart/update/<int:item_id>/",
        views.update_cart_quantity,
        name="update_cart_quantity",
    ),
    path("add-review/<int:product_id>/", views.add_review, name="add_review"),
    path("payment-complete/", views.payment_complete, name="payment_complete"),
    path("wishlist/add/", views.add_to_wishlist, name="add_to_wishlist"),
    path("wishlist/", views.wishlist, name="wishlist"),
    path(
        "wishlist/remove/<int:product_id>",
        views.remove_from_wishlist,
        name="remove_from_wishlist",
    ),
    path("apply_coupon/", views.apply_coupon, name="apply_coupon"),
    path("remove_coupon/", views.remove_coupon, name="remove_coupon"),
    path(
        "return-request/<int:order_item_id>/",
        views.return_request,
        name="return_request",
    ),
    path("return-request-list/", views.return_request_list, name="return_request_list"),
    path("notifications/", views.user_notifications, name="notifications"),
    path(
        "notification/mark-as-read/<int:notification_id>/",
        views.mark_notification_as_read,
        name="mark_notification_as_read",
    ),
]
