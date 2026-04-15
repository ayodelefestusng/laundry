import base64
import json
import logging
import traceback
from datetime import date, timedelta
from io import BytesIO

import qrcode
import requests
from django.core.signing import Signer
from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings
import functools

logger = logging.getLogger(__name__)



def get_signed_token(data):
    """
    Returns a cryptographically signed version of the data.
    """
    signer = Signer()
    return signer.sign(str(data))


def calculate_expected_delivery(items):
    max_days = max(item.delivery_days for item in items)
    return date.today() + timedelta(days=max_days)



def generate_qr_base64(data, sign=True):
    """
    Generates a base64 encoded QR code image string.
    If sign is True, it appends a cryptographic signature to the data.
    """
    if sign:
        signer = Signer()
        data = signer.sign(data)
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, "PNG")
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

def verify_qr_token(token):
    """
    Verifies a signed QR token and returns the original data.
    Returns None if verification fails.
    """
    signer = Signer()
    try:
        return signer.unsign(token)
    except Exception:
        return None



# Ollama and AI Utilities

class OllamaCloudWrapper:
    def __init__(self, model_name, host, api_key):
        self.model_name = model_name
        self.host = host
        self.api_key = api_key

    def invoke(self, prompt):
        """
        Sends a prompt to the Ollama Cloud API.
        """
        try:
            url = f"{self.host.rstrip('/')}/api/generate"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False
            }
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            return response.json().get('response', '')
        except Exception as e:
            logging.error(f"Ollama AI Error: {str(e)}\n{traceback.format_exc()}")
            return None

def analyze_sentiment(text):
    """
    Analyzes sentiment using the Ollama model. Returns a score from -2 to 2.
    """
    if not text:
        return "0"
    
    API_KEY = "3f86151ac944457b9a4519285efbcda7.FbvjhXHFFD8kW6NFhn-3Ebx5"
    model = OllamaCloudWrapper(
        model_name="gpt-oss:120b",
        host="https://ollama.com",
        api_key=API_KEY
    )
    
    prompt = (
        f"Analyze the sentiment of this laundry service feedback: '{text}'. "
        "Return ONLY a single integer score from -2 (very negative) to 2 (very positive)."
    )
    
    result = model.invoke(prompt)
    if result:
        return result.strip()
    return "0"

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
