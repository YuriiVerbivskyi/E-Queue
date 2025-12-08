import os
import requests
from django.core.mail import send_mail
from django.conf import settings
from .models import Notification


def send_notification_email(user, subject, message, notification_type="registration"):
    Notification.objects.create(
        user=user,
        notification_type=notification_type,
        subject=subject,
        message=message,
    )

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True,
        )
    except Exception as e:
        print(f"Error sending email: {e}")