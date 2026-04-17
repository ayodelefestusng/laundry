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



# utils/bi_engine.py
from django.db.models import Count, Sum, Avg, F, ExpressionWrapper, fields
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
from .models import Order, WorkflowInstance, OrderItem


import googlemaps
import logging
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)
from django.utils.dateparse import parse_date
from datetime import datetime, time



class GeocodingService:
    def __init__(self):
        self.gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)

    def resolve_location_name(self, lat, lng):
        """
        Converts coordinates to a friendly neighborhood/city name.
        Uses a cache to save API costs.
        """
        # Round to 3 decimal places to group nearby orders (~110m)
        cache_key = f"geo_{round(float(lat), 3)}_{round(float(lng), 3)}"
        cached_name = cache.get(cache_key)
        
        if cached_name:
            return cached_name

        try:
            # result_type='neighborhood|political' helps get the area name 
            # rather than a specific street address for cleaner BI reports
            reverse_geocode_result = self.gmaps.reverse_geocode(
                (lat, lng), 
                result_type=['neighborhood', 'political', 'locality']
            )

            if reverse_geocode_result:
                # We pick the first formatted address or a specific component
                address = reverse_geocode_result[0]['formatted_address']
                # Cache for 30 days - location names rarely change
                cache.set(cache_key, address, 60*60*24*30)
                return address
        except Exception as e:
            logger.error(f"Google Geocoding Error: {e}")
        
        return f"Zone ({lat}, {lng})"
    
    
class WorkflowBI:
    def __init__(self, tenant, start_date=None, end_date=None):
        self.tenant = tenant
        
        # 1. Handle Start Date
        if isinstance(start_date, str) and start_date:
            parsed_s = parse_date(start_date)
            if parsed_s:
                # Use .combine only if parsed_s is not None
                self.start_date = timezone.make_aware(datetime.combine(parsed_s, time.min))
            else:
                self.start_date = timezone.now() - timedelta(days=30)
        else:
            self.start_date = timezone.now() - timedelta(days=30)

        # 2. Handle End Date
        if isinstance(end_date, str) and end_date:
            parsed_e = parse_date(end_date)
            if parsed_e:
                self.end_date = timezone.make_aware(datetime.combine(parsed_e, time.max))
            else:
                self.end_date = timezone.now()
        else:
            # If no end date, default to end of today
            self.end_date = timezone.now().replace(hour=23, minute=59, second=59)

        self.geo_service = GeocodingService()
    def get_dashboard_stats(self):
        # Caching the whole stats object for 15 minutes to save DB hits
        cache_key = f"bi_stats_{self.tenant.id}_{self.start_date}_{self.end_date}"
        data = cache.get(cache_key)
        if data:
            return data

        # 1. Revenue Analytics
        revenue_data = Order.objects.filter(
            tenant=self.tenant, created_at__range=(self.start_date, self.end_date)
        ).aggregate(
            total_rev=Sum('total_price'),
            avg_order=Avg('total_price'),
            count=Count('id')
        )

        # 2. Workflow Efficiency (Turnaround Time)
        # We calculate the difference between completion and initiation
        tat_data = WorkflowInstance.objects.filter(
            tenant=self.tenant, 
            completed_at__isnull=False,
            created_at__range=(self.start_date, self.end_date)
        ).annotate(
            duration=ExpressionWrapper(
                F('completed_at') - F('created_at'),
                output_field=fields.DurationField()
            )
        ).aggregate(avg_tat=Avg('duration'))

        # 3. Status Distribution (For Pie Charts)
        status_distribution = list(Order.objects.filter(tenant=self.tenant)
            .values('status')
            .annotate(total=Count('status')))

        data = {
            "revenue": revenue_data,
            "avg_tat_hours": tat_data['avg_tat'].total_seconds() / 3600 if tat_data['avg_tat'] else 0,
            "status_dist": status_distribution,
            "labels": [item['status'] for item in status_distribution],
            "values": [item['total'] for item in status_distribution],
        }
        
        cache.set(cache_key, data, 900) # 15 min cache
        return data
    
    def get_top_customers(self, limit=5):
        """Logic for Top 5 (or N) Customers"""
        return Order.objects.filter(
            tenant=self.tenant,
            created_at__range=(self.start_date, self.end_date)
        ).values('customer_email', 'customer_phone') \
         .annotate(
            order_count=Count('id'),
            total_revenue=Sum('total_price'),
            avg_revenue=Avg('total_price')
        ).order_by('-total_revenue')[:limit]

    def get_top_locations(self, limit=5):
        """Logic for Top Order Hubs using Google API"""
        # Group by coordinates
        top_coords = Order.objects.filter(
            tenant=self.tenant,
            pickup_latitude__isnull=False,
            created_at__range=(self.start_date, self.end_date)
        ).values('pickup_latitude', 'pickup_longitude') \
         .annotate(
            count=Count('id'),
            revenue=Sum('total_price')
        ).order_by('-count')[:limit]

        # Resolve names for the top results
        for item in top_coords:
            item['location_name'] = self.geo_service.resolve_location_name(
                item['pickup_latitude'], 
                item['pickup_longitude']
            )
        
        return top_coords