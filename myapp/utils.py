from datetime import date, timedelta

import base64
from io import BytesIO
import qrcode


def calculate_expected_delivery(items):
    max_days = max(item.delivery_days for item in items)
    return date.today() + timedelta(days=max_days)



def generate_qr_base64(data):
    """Generates a base64 encoded QR code image string."""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


import functools

from django.shortcuts import redirect
from django.urls import reverse

from .models import CustomUser


def is_admin(view_func):
    """
    Decorator to check if the user is an admin (staff member).
    If not, it redirects them to the homepage.
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_staff:
            return view_func(request, *args, **kwargs)
        else:
            return redirect(reverse('homepage'))
    return wrapper
