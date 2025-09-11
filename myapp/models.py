from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)

    # Add related_name to resolve clashes
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
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name

class ServiceType(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name

class Service(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, default=1, related_name='services')
    # category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, default=1)
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE, related_name='services')
    price = models.DecimalField(max_digits=6, decimal_places=2)
    delivery_time_days = models.IntegerField(help_text="Estimated delivery time in days.")
    def __str__(self):
        return f"{self.name} - {self.service_type}"

ORDER_STATUS = (
    ('pending_invoice', 'Pending Invoice'),
    ('invoice_sent', 'Invoice Sent'),
    ('payment_received', 'Payment Received'),
    ('in_progress', 'In Progress'),
    ('ready_for_pickup', 'Ready for Pickup'),
    ('delivered', 'Delivered'),
    ('canceled', 'Canceled'),
)

ITEM_STATUS = (
    ('pending', 'Pending'),
    ('in_progress', 'In Progress'),
    ('completed', 'Completed'),
)

class Order(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending_invoice')
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
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, choices=ITEM_STATUS, default='pending')
    price = models.DecimalField(max_digits=6, decimal_places=2)
    delivery_time_days = models.IntegerField()

class Comment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='comments')
    body = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Comment on Order #{self.order.id}"
