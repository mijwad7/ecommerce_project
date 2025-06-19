from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse

class BlockUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if user is authenticated and blocked
        if request.user.is_authenticated and request.user.is_blocked:
            logout(request)
            messages.error(request, "Your account has been blocked. Please contact support.")
            return redirect(reverse('app:user_login'))

        response = self.get_response(request)
        return response