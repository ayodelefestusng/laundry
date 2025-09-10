from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser

# Custom User Model
class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    is_staff = models.BooleanField(default=False)
    is_customer = models.BooleanField(default=True)
    # Add other fields as needed


from django.db import models
from django.contrib.auth.models import User



# Service Choices
SERVICE_CHOICES = (
    ('wash', 'Washing'),
    ('iron', 'Ironing'),
    ('dry_clean', 'Dry Cleaning'),
)

# Workflow Stages
WORKFLOW_STAGES = (
    ('pending_dispatch', 'Pending Dispatch'),
    ('in_transit', 'In Transit'),
    ('at_facility', 'At Facility'),
    ('washing', 'Washing'),
    ('drying', 'Drying'),
    ('ironing', 'Ironing'),
    ('packaging', 'Packaging'),
    ('ready_for_pickup', 'Ready for Pickup/Dispatch'),
    ('completed', 'Completed'),
)

# Order Status
ORDER_STATUS = (
    ('pending_review', 'Pending Customer Review'),
    ('accepted', 'Accepted by Customer'),
    ('commented', 'Commented by Customer'),
    ('in_progress', 'In Progress'),
    ('ready_for_delivery', 'Ready for Delivery'),
    ('delivered', 'Delivered'),
)

class CustomerRequest(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    address = models.TextField()
    contact_number = models.CharField(max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=ORDER_STATUS, default='pending_review')
    comment = models.TextField(blank=True, null=True)
    batch_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    is_active = models.BooleanField(default=True)

class LaundryItem(models.Model):
    request = models.ForeignKey(CustomerRequest, related_name='items', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    service_type = models.CharField(max_length=50, choices=SERVICE_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    delivery_time_days = models.IntegerField()
    qr_code_data = models.CharField(max_length=255, unique=True, blank=True, null=True)
    current_stage = models.CharField(max_length=50, choices=WORKFLOW_STAGES, default='at_facility')
    qr_code_base64 = models.TextField(blank=True, null=True)

class WorkflowHistory(models.Model):
    item = models.ForeignKey(LaundryItem, on_delete=models.CASCADE)
    stage = models.CharField(max_length=50, choices=WORKFLOW_STAGES)
    timestamp = models.DateTimeField(auto_now_add=True)