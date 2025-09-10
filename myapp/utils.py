from datetime import timedelta, date

def calculate_expected_delivery(items):
    max_days = max(item.delivery_days for item in items)
    return date.today() + timedelta(days=max_days)


import qrcode
import base64
from io import BytesIO

def generate_qr_base64(data):
    """Generates a base64 encoded QR code image string."""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode('utf-8')