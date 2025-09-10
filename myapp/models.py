from django.db import models
from django.contrib.auth.models import AbstractUser

# ==============================================================================
#  Choice Tuples
# ==============================================================================

# Service Choices
SERVICE_CHOICES = (
    ('wash', 'Washing'),
    ('iron', 'Ironing'),
    ('dry_clean', 'Dry Cleaning'),
)

# Workflow Stages for a single laundry item
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

# Order Status for the entire customer request
ORDER_STATUS = (
    ('pending_review', 'Pending Customer Review'),
    ('accepted', 'Accepted by Customer'),
    ('commented', 'Commented by Customer'),
    ('in_progress', 'In Progress'),
    ('ready_for_delivery', 'Ready for Delivery'),
    ('delivered', 'Delivered'),
)

# ==============================================================================
#  Model Definitions
# ==============================================================================

# Custom User Model to add more fields
class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    is_staff = models.BooleanField(default=False)
    is_customer = models.BooleanField(default=True)



class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


# Service model to link a category with a service type, price, and delivery time


class Service(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='services')
    service_type = models.CharField(max_length=50, choices=SERVICE_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_time_days = models.IntegerField()

    class Meta:
        unique_together = ('category', 'service_type')

    def __str__(self):
        return f"{self.category.name} - {self.get_service_type_display()}"

# CustomerRequest model to store the overall order details
class CustomerRequest(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    address = models.TextField()
    contact_number = models.CharField(max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=ORDER_STATUS, default='pending_review')
    comment = models.TextField(blank=True, null=True)
    batch_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    is_active = models.BooleanField(default=True)

# LaundryItem model to represent individual items within a request
class LaundryItem(models.Model):
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True)
    request = models.ForeignKey(CustomerRequest, related_name='items', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=100)
    qr_code_base64 = models.TextField(blank=True, null=True)
    
    @property
    def price(self):
        return self.service.price if self.service else None

    @property
    def delivery_time_days(self):
        return self.service.delivery_time_days if self.service else None

    def __str__(self):
        return f"{self.name} ({self.color})"


# WorkflowHistory model to track the status of each individual item
class WorkflowHistory(models.Model):
    item = models.ForeignKey(LaundryItem, on_delete=models.CASCADE)
    stage = models.CharField(max_length=50, choices=WORKFLOW_STAGES)
    timestamp = models.DateTimeField(auto_now_add=True)