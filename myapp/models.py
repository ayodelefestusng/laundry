from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.conf import settings

class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_set',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_permissions_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

class ServiceCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.name

SERVICE_CHOICES = (
    ('wash_fold', 'Wash & Fold'),
    ('dry_clean', 'Dry Cleaning'),
    ('ironing', 'Ironing'),
)

class Service(models.Model):
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name='services')
    service_type = models.CharField(max_length=50, choices=SERVICE_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_time_days = models.IntegerField(help_text="Estimated delivery time in days.")

    class Meta:
        unique_together = ('category', 'service_type')

    def __str__(self):
        return f"{self.category.name} - {self.get_service_type_display()}"

ORDER_STATUS = (
    ('pending', 'Pending'),
    ('in_progress', 'In Progress'),
    ('ready_for_pickup', 'Ready for Pickup'),
    ('delivered', 'Delivered'),
    ('canceled', 'Canceled'),
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

class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    customer_name = models.CharField(max_length=100, blank=True, null=True)
    customer_email = models.EmailField(blank=True, null=True)
    customer_phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    pickup_date = models.DateField(default=timezone.now)
    special_instructions = models.TextField(blank=True, null=True)
    total_price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    estimated_delivery_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='order_items')
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, choices=WORKFLOW_STAGES, default='pending_dispatch')

class Comment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments', null=True, blank=True)
    body = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment on Order #{self.order.id}"
