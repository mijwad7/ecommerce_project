from django.core.mail import send_mail
from .models import EmailOTPDevice

def send_otp_to_email(user, force_resend=False):
    # Create or get an existing OTP device for the user
    device, created = EmailOTPDevice.objects.get_or_create(user=user)

    # If OTP is not expired or forced resend is true, generate a new OTP
    if device.is_otp_expired() or force_resend:
        otp_code = device.generate_otp()
        
        # Send OTP via email
        subject = "Your ShopHive Account OTP Code"
        message = f"Welcome to ShopHive. Your OTP code is {otp_code}. It is valid for {EmailOTPDevice.OTP_EXPIRY_MINUTES} minutes."
        send_mail(subject, message, 'mijuzzuae@gmail.com', [user.email])
        return True  # Indicates a new OTP was sent
    return False  # No new OTP was sent
