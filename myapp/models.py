# Create your models here.
import logging
from math import log
from pyclbr import Class
import random
import uuid
from attr import has
from django.db import models, transaction
import logging
from django.db import models, transaction

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string
import uuid
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from decimal import Decimal
from django.db import models
# org/managers.py
from django.db import models
import logging
import sys
import os
from logging.handlers import RotatingFileHandler

from matplotlib.pylab import qr




from .middleware import _thread_locals



logger = logging.getLogger(__name__)
# logger = logging.getLogger("HR_AGENT")
logger.propagate = True 

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "laundry.log")

if not logger.handlers:
    logging.captureWarnings(True)
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:%(lineno)d - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=0, encoding="utf-8"),
        ],
        force=True,
    )
    
    

logger.propagate = True # Flow to root logger for persistence

# Suppress noisy libraries
logging.getLogger("watchfiles").setLevel(logging.WARNING)
logging.getLogger("aiosqlite").setLevel(logging.INFO)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("langsmith").setLevel(logging.INFO)

def log_with_context(level, message, user):
    tenant = getattr(user, "tenant", "Global")
    username = getattr(user, "username", None) or str(user)
    logger.log(level, f"tenant={tenant}|user={username}|{message}")
# Auth user model instance
# ✅ Valid Nigerian phone prefixes (4-digit only)
VALID_PREFIXES = {
    '0809', '0817', '0818', '0909', '0908',  # 9mobile
    '0701', '0708', '0802', '0808', '0812', '0901', '0902', '0904', '0907', '0912', '0911',  # Airtel
    '0705', '0805', '0807', '0811', '0815', '0905', '0915',  # Glo
    '0804',  # Mtel
    '0703', '0706', '0803', '0806', '0810', '0813', '0814', '0816', '0903', '0906', '0913', '0916', '0704', '0707'  # MTN
}

# 📞 Validator for Nigerian phone prefixes
def validate_nigerian_phone(value):
    if not value.isdigit():
        raise ValidationError("Phone number must contain only digits.")
    if len(value) != 11:
        raise ValidationError("Phone number must be exactly 11 digits.")
    if value[:4] not in VALID_PREFIXES:
        raise ValidationError(f"Phone number must start with a valid Nigerian prefix. Got '{value[:4]}'.")




class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        # Pass extra_fields (like 'name') into the model constructor
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, phone=None, **extra_fields):
        user = self.create_user(email, password, **extra_fields)
        user.is_superuser = True
        user.is_staff = True
        if phone:
            user.phone = phone  
        user.save(using=self._db)
        return user



class CustomUser(AbstractBaseUser, PermissionsMixin):
    username = None  # 👈 Explicitly remove username field
    tenant = models.ForeignKey(
        "Tenant", on_delete=models.PROTECT, null=True, blank=True  # allow NULL
    )

    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True, validators=[validate_nigerian_phone])
    state = models.ForeignKey('State', on_delete=models.SET_NULL, null=True, blank=True)
    town = models.ForeignKey('Town', on_delete=models.SET_NULL, null=True, blank=True)
    address = models.CharField(max_length=255, blank=True, null=True, help_text="House/Street address")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    line_manager = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="downline")
    deputy_person = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="deputy_for", help_text="Deputy head for automatic delegation.")

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    is_seller = models.BooleanField(default=False)
    is_buyer = models.BooleanField(default=True)

    mfa_secret = models.CharField(max_length=16, blank=True, null=True)
    mfa_enabled = models.BooleanField(default=False)

    groups = models.ManyToManyField(
        "auth.Group",
        related_name="myapp_users",
        blank=True,
        help_text="The groups this user belongs to.",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="myapp_user_permissions",
        blank=True,
        help_text="Specific permissions for this user.",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    objects = CustomUserManager()
    # Add this to your User model in user/models.py

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    @property
    def is_employee(self):
        return self.groups.filter(name="Employee").exists()

    @property
    def is_hr_officer(self):
        return self.groups.filter(name="HR Officer").exists()

    @property
    def is_manager(self):
        return self.groups.filter(name="Manager").exists()

    @property
    def is_hr_manager(self):
        return self.groups.filter(name="HR Manager").exists()

    @property
    def is_hr_admin(self):
        return self.groups.filter(name="HR Admin").exists()



# class CustomUser1(AbstractBaseUser, PermissionsMixin):
#     email = models.EmailField(unique=True)
#     name =models.CharField( max_length=50,null=True)
#     phone = models.IntegerField()
#     is_active = models.BooleanField(default=True)
#     is_staff = models.BooleanField(default=False)

#     USERNAME_FIELD = "email"
#     phone = models.IntegerField(null=True, blank=True)

#     objects = CustomUserManager()

#     def __str__(self):
#         return self.email


# from .managers import CustomUserManager
ORDER_STATUS = (
    ('pending', 'Pending'),
     ('invoice_sent', 'Invoice Sent'),
    ('commented', 'Commented'),
    ('confirmed', 'Confirmed Order'),
    ('in_progress', 'In Progress'),
    ('ready_for_dispatch', 'Ready for Dispatch'),
    ('awaiting_dispatch', 'Awaiting Dispatch'),
    ('assigned_to_dispatcher', 'Assigned to Dispatcher'),
    ('paid', 'Paid'),
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



# class CustomUser(AbstractUser):
#     username = None
#     email = models.EmailField('email address', unique=True)
#     phone_number = models.CharField(max_length=15, blank=True, null=True)
#     address = models.CharField(max_length=255, blank=True, null=True)
#     USERNAME_FIELD = 'email'
#     REQUIRED_FIELDS = []
#     objects = CustomUserManager()
#     groups = models.ManyToManyField(
#         'auth.Group',
#         related_name='customuser_set',
#         blank=True,
#         help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
#         verbose_name='groups',
#     )
#     user_permissions = models.ManyToManyField(
#         'auth.Permission',
#         related_name='customuser_permissions_set',
#         blank=True,
#         help_text='Specific permissions for this user.',
#         verbose_name='user permissions',
#     )
#     def __str__(self):
#         return self.email

def tenant_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/tenant_<id>/<model_name>/filename
    # For Tenant model itself, use instance.id; for other models, use instance.tenant.id
    model_name = instance.__class__.__name__.lower()
    tenant_id = instance.id if model_name == "tenant" else instance.tenant.id
    return f"tenant_{tenant_id}/{model_name}/{filename}"




from django.db.models.signals import post_save
from django.dispatch import receiver

# Add post_save signal for Partner Assignment
@receiver(post_save, sender=CustomUser)
def assign_partner_group(sender, instance, created, **kwargs):
    if created and instance.tenant and instance.is_staff and not instance.is_superuser:
        from django.contrib.auth.models import Group
        group, _ = Group.objects.get_or_create(name='Partner')
        instance.groups.add(group)

class State(models.Model):
    name = models.CharField(max_length=100, unique=True)
    class Meta:
        ordering = ['id']
    def __str__(self):
        return self.name

class Town(models.Model):
    name = models.CharField(max_length=100)
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='towns')
    class Meta:
        ordering = ['id']
        unique_together = ('name', 'state')
    def __str__(self):
        return f"{self.name}, {self.state.name}"

class TenantManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        
        # If the thread has a tenant_id, filter by it automatically
        tenant_id = getattr(_thread_locals, 'tenant_id', None)
        
        # We skip filtering for superusers or if no tenant is set (e.g. background tasks)
        if tenant_id and not getattr(_thread_locals, 'is_superuser', False):
            return qs.filter(tenant_id=tenant_id)
        
        return qs

class Tenant(models.Model):
    name = models.CharField(max_length=255,default="Dignity", help_text="Tenant name, e.g., Dignity")
    code = models.CharField(
        max_length=50,
        unique=True,
        default="DMC",
        help_text="Short unique code for the tenant (e.g., MSFT)",
    )
    subdomain = models.CharField(max_length=50, unique=True, default="127.0.0.1", help_text="Subdomain for the tenant (e.g., dignity)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.code})"

class TenantModel(models.Model):
    # tenant = models.ForeignKey('org.Tenant', on_delete=models.CASCADE)
    tenant = models.ForeignKey(
       Tenant, on_delete=models.CASCADE, null=True, blank=True
    )

    # Use the custom manager
    objects = TenantManager()
    # Keep the original manager for cases where you NEED to see all data
    all_objects = models.Manager()

    class Meta:
        abstract = True

class TenantAttribute(TenantModel):
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name='attribute')
    brand_name = models.CharField(max_length=210, default="Dignity", help_text="Brand name , e.g., Dignity")
    
    logo = models.ImageField(upload_to=tenant_directory_path, null=True, blank=True, help_text="Primary logo for the tenant (displayed in header)")
    favicon = models.ImageField(upload_to=tenant_directory_path, null=True, blank=True, help_text="Tenant-specific favicon")
    primary_color = models.CharField(max_length=7, default="#4f46e5", help_text="Brand primary color (Hex), e.g., #4f46e5")
    secondary_color = models.CharField(max_length=7, default="#6366f1", help_text="Brand secondary color (Hex), e.g., #6366f1")
    font_family = models.CharField(max_length=255, default="'Inter', sans-serif", help_text="CSS Font family for the tenant")
    custom_css = models.TextField(blank=True, help_text="Custom CSS overrides for this tenant")

    component_restrictions = models.CharField(max_length=50, default="NG", help_text="ISO country code for Places API")
    strict_bounds = models.BooleanField(default=True)
    
    southwest_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    southwest_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    northeast_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    northeast_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    location_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    whatsapp_number = models.CharField(max_length=20, default="+2349068770054", help_text="WhatsApp phone number")
    address = models.CharField(max_length=255, blank=True, null=True, help_text="Tenant physical address")

    def __str__(self):
        return f"{self.tenant.name} Attributes"

    # def __str__(self):
    #     return f"{self.name} ({self.code})"



class Cluster(TenantModel):
    name = models.CharField(max_length=100)
    towns = models.ManyToManyField(Town, related_name='clusters')
    
    
    class Meta:
        ordering = ["name"]
        unique_together = ("name", "tenant")
    def __str__(self):
        return f"{self.name} Cluster"

    
    def clean(self):
        super().clean()
        
        # Only perform Many-to-Many validation if the object has been saved
        if self.pk:
            try:
                # Restrict towns to those in clusters AND under the selected state
                for town in self.towns.all():
                    if Cluster.objects.filter(tenant=self.tenant, towns=town).exclude(pk=self.pk).exists():
                        raise ValidationError(
                            {"towns": f"Town '{town.name}' is already assigned to another cluster for this tenant."}
                        )
            except ValidationError:
                # Re-raise validation errors so Django can catch them
                raise
            except Exception as e:
                logger.error(f"Unexpected error during Cluster validation for ID {self.pk}: {e}")
                raise ValidationError("An unexpected error occurred during validation.")
 
                
class DeliveryPricing(TenantModel):
    """Cluster-based pricing."""
    cluster = models.ForeignKey(Cluster, on_delete=models.CASCADE, related_name='delivery_prices', null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Delivery Pricing"
        verbose_name_plural = "Delivery Pricing Tiers"

    def __str__(self):
        return f"{self.cluster.name}: {self.price}"

class PremiumClient(TenantModel):
    name = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, unique=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    def __str__(self):
        return self.name


class ServiceCategory(TenantModel):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name

class ServiceChoices(TenantModel):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name
   



    
     
    
    
    
    
    
WORKFLOW_STAGES1 = (
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


class Package(TenantModel):
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name='services')
    service_type = models.ForeignKey(ServiceChoices, on_delete=models.SET_NULL, null=True, blank=True, related_name='packages')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_time_days = models.IntegerField(help_text="Estimated delivery time in days.")
    class Meta:
        unique_together = ('category', 'service_type')
    def __str__(self):
        return f"{self.category.name}-{self.id} - {self.service_type.name if self.service_type else 'Uncategorized'}"

def generate_order_code():
    return get_random_string(8).upper()
  
QR_STATUS_CHOICES = (
    ('unused', 'Unused'),
    ('assigned', 'Assigned'),
    ('invalid', 'Invalid'),
)

class QR(TenantModel):
    code = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=QR_STATUS_CHOICES, default='unused')
    # order_item = models.OneToOneField('OrderItem', on_delete=models.CASCADE, related_name='qr_codes', null=True, blank=True)
    def __str__(self):
        return f"{self.code}  in Order #{self.status}"
    
    
class Order(TenantModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    # order_code = models.CharField(max_length=12, unique=False, editable=True, default=get_random_string(8).upper)
    # order_code = models.CharField(max_length=12, unique=True, blank=True, null=True)
    order_code = models.CharField(max_length=12, unique=True,  editable=True, default=generate_order_code)
    # user = models.ForeignKey(CustomUser, on_delete=models.SET_DEFAULT, default="missing_id",related_name='laundry_orders')
    status = models.CharField(max_length=120, choices=ORDER_STATUS, default='pending')
    customer_name = models.CharField(max_length=100, blank=True, null=True)
    customer_email = models.EmailField(blank=True, null=True)
    customer_phone = models.CharField(max_length=15, blank=True, null=True)
    state = models.ForeignKey('State', on_delete=models.SET_NULL, null=True, blank=True, related_name='pickup_orders')
    town = models.ForeignKey('Town', on_delete=models.SET_NULL, null=True, blank=True, related_name='pickup_orders')
    address = models.CharField(max_length=255, blank=True, null=True, help_text="House/Street address")
    pickup_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    pickup_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    # pickup_date = models.DateField(default=timezone.now)
    pickup_date = models.DateTimeField(default=timezone.now)

    special_instructions = models.TextField(blank=True, null=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    estimated_delivery_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    has_confirmation_received=models.BooleanField(default=False)
    has_invoice_sent=models.BooleanField(default=False)
    has_payment_received=models.BooleanField(default=False)
    has_comment_from_customer=models.BooleanField(default=False)
    work_initiator = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, related_name="initiated_orders", null=True, blank=True, limit_choices_to={'is_staff': True}
    )
    
    # Dispatch & Delivery Fields
    dispatched_by = models.CharField(max_length=255, blank=True, null=True)
    delivered_by = models.CharField(max_length=255, blank=True, null=True)
    received_by_name = models.CharField(max_length=255, blank=True, null=True)
    received_by_phone = models.CharField(max_length=50, blank=True, null=True)
    sentiment_analysis = models.CharField(max_length=50, blank=True, null=True, help_text="Sentiment analysis label/score")
    qr_secure_token = models.CharField(max_length=255, unique=True, null=True, blank=True)
    
    # New Fields for Advanced Order Management
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="laundry_orders")
    delivery_option = models.CharField(
        max_length=20, 
        choices=[('home_delivery', 'Home Delivery'), ('on_premise', 'On-Premise Pickup')], 
        default='home_delivery'
    )
    shipping_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Recipient Info (for Home Delivery)
    recipient_name = models.CharField(max_length=100, blank=True, null=True)
    recipient_email = models.EmailField(blank=True, null=True)
    recipient_phone = models.CharField(max_length=15, blank=True, null=True)
    recipient_state = models.ForeignKey('State', on_delete=models.SET_NULL, null=True, blank=True, related_name='delivery_orders')
    recipient_town = models.ForeignKey('Town', on_delete=models.SET_NULL, null=True, blank=True, related_name='delivery_orders')
    recipient_address = models.CharField(max_length=255, null=True, blank=True, help_text="House/Street address")
    recipient_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    recipient_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    def check_and_update_status(self, user=None):
        """
        Logic to transition order to 'in_progress' if all items have QR codes.
        """
        try:
            items = self.items.all()
            if not items.exists():
                return False

            # Efficiently check if any item is missing a QR code
            # This is faster than a Python loop for large orders
            any_missing = items.filter(
                models.Q(qr_code__isnull=True) | models.Q(qr_code='')
            ).exists()

            if not any_missing and self.status != 'in_progress':
                self.status = 'in_progress'
                self.has_confirmation_received = True

                # Determine the latest updated item to adopt its qr_initiator
                latest_item = items.order_by('-updated_at').first()
                if latest_item and latest_item.qr_initiator:
                    self.work_initiator = latest_item.qr_initiator
                elif user and user.is_staff:
                    self.work_initiator = user
                else:
                    self.work_initiator = CustomUser.objects.filter(tenant=self.tenant, is_staff=True).first()

                self.save(update_fields=['status', 'has_confirmation_received', 'updated_at', 'work_initiator'])
                logger.info(f"Order {self.order_code} transitioned to in_progress. Initiator: {self.work_initiator}")
                
                # --- TRIGGER WORKFLOWS FOR EACH ORDER ITEM ---
                initiator = self.work_initiator
                logger.info(f"Initiating workflow trigger for Order {self.order_code} with initiator {initiator}.")
                if items.exists():
                    order_item_ct = ContentType.objects.get_for_model(items.first())
                    for item in items:
                        workflow = item.package.workflows.first()
                        if workflow:
                            # Prevent duplicate workflow instance creation
                            if not WorkflowInstance.objects.filter(content_type=order_item_ct, object_id=item.id).exists():
                                logger.info(f"Starting workflow '{workflow.name}' for OrderItem {item.id} (Package: {item.package}).")
                                first_stage = workflow.stages.order_by('sequence').first()
                                if first_stage and initiator:
                                    WorkflowInstance.objects.create(
                                        tenant=self.tenant,
                                        workflow=workflow,
                                        content_type=order_item_ct,
                                        object_id=item.id,
                                        current_stage=first_stage,
                                        initiated_by=initiator
                                    )
                                    logger.info(f"Triggered workflow '{workflow.name}' for OrderItem {item.id}")
                                else:
                                    val = "stages" if not first_stage else "initiator"
                                    logger.warning(f"Could not start workflow '{workflow.name}': Missing {val}.")
                        else:
                            logger.info(f"No workflow attached to Package for OrderItem {item.id}")

                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error updating status for Order {self.id}: {str(e)}", exc_info=True)
            return False
    def __str__(self):
        return f"Order #for {self.customer_email}"


class OrderItem(TenantModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name='order_items')
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=50, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    delivery_time_days = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=WORKFLOW_STAGES, default='pending_dispatch')
    qr_code = models.CharField(max_length=100, unique=True, blank=True, null=True)
    
    qr_initiator = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, related_name="qr_assigned_items", null=True, blank=True, limit_choices_to={'is_staff': True}
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def save(self, *args, **kwargs):
        try:
            # Atomic transaction to ensure data integrity during the double save
            with transaction.atomic():
                is_new_qr = False
                
                if self.pk:
                    old_instance = OrderItem.objects.filter(pk=self.pk).first()
                    if old_instance and not old_instance.qr_code and self.qr_code:
                        is_new_qr = True
                elif self.qr_code:
                    is_new_qr = True

                super().save(*args, **kwargs)

                # If a QR code was just added, trigger the check on the parent Order
                if is_new_qr:
                    self.order.check_and_update_status()

        except Exception as e:
            logger.error(f"Failed to save OrderItem or update Order status: {str(e)}", exc_info=True)
            raise e
    
    def __str__(self):
        return f"{self.name}  in Order #{self.order.id}"

class WorkflowHistory(TenantModel):
    item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='workflow_history')
    from_stage = models.CharField(max_length=50, blank=True, null=True)
    to_stage = models.CharField(max_length=50)
    actor = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='actions_performed', limit_choices_to={'is_staff': True})
    previous_actor = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='previous_actions', limit_choices_to={'is_staff': True})
    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=50, help_text="Accept, Reject, Escalate, etc.")

    def __str__(self):
        return f"{self.item.name} moved to {self.to_stage} by {self.actor}"

ACTOR = (
    ('customer', 'Csutomer'),
     ('staff', 'Staff'),

)

class Comment(TenantModel):
    order = models.ForeignKey(Order, 
        on_delete=models.SET_NULL, 
        related_name='comments', 
        null=True, 
        blank=True)
    actor=models.CharField(max_length=20, choices=ACTOR, default='customer')
    # user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments', null=True, blank=True)
    body = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Comment on Order #{self.order.id}"



class Payment(TenantModel):
    """Tracks Paystack transactions."""
    # order = models.ForeignKey(Order, on_delete=models.SET_NULL)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    amount = models.IntegerField() # In kobo
    reference = models.CharField(max_length=100, unique=True)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Payment for {self.order.user.name} - {self.reference}"
    
class Workflow(TenantModel):
    """Defines a process (e.g., 'Annual Leave Process')"""
    service=models.ForeignKey(Package, on_delete=models.CASCADE, related_name='workflows', null=True, blank=True)
    name = models.CharField(max_length=255, help_text="Descriptive name of the workflow, e.g., 'Annual Leave Process'")
    code = models.SlugField(
        help_text="Defines code of the workflow eg 'leave-approval'"
    )  # e.g., 'leave-approval'
 

    def __str__(self):
        return (
            f"{self.name} - code {self.code}"
        )

    class Meta:
        # ordering = ["last_name", "first_name"]
        verbose_name = "Workflow Record"
        verbose_name_plural = "Workflow Records"
        # indexes = [
        #     models.Index(fields=["first_name", "last_name", "tenant"]),
        #     models.Index(fields=["employee_email", "tenant"]),
        # ]
class WorkflowStage(TenantModel):
    """
    Represents a step in the workflow with time-based escalation logic.
    """

    workflow = models.ForeignKey(
        Workflow, on_delete=models.CASCADE, related_name="stages"
    )
    # Changed from CharField to ForeignKey as requested
    responsible_officer = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name="approver_stages",
        help_text="The employee responsible for handling this stage.",
        limit_choices_to={'is_staff': True}
    )
    # name = models.CharField(max_length=255, choices=WORKFLOW_STAGES, help_text="Descriptive name of the stage, e.g., 'Manager Approval'")
    service_action = models.ForeignKey(
    ServiceChoices,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    help_text="Descriptive name of the stage, e.g., 'In Washing'"
)
    sequence = models.PositiveIntegerField(
        help_text="Order of execution (e.g., 1, 2, 3)"
    )
    turnaround_time = models.PositiveIntegerField(
        default=24, help_text="Maximum hours allowed for action before escalation."
    )
    is_final_stage = models.BooleanField(default=False)

    # Required for the Dashboard weight logic we built earlier

    completed_status = models.BooleanField(default=False)

    class Meta:
        ordering = ["sequence"]
        unique_together = ("workflow", "sequence", "tenant")

    
    def clean(self):
        super().clean()
        if self.sequence < 1:
            raise ValidationError("Sequence must start from 1.")
        
        # FIX: Only run the database filter if the parent workflow already exists
        if self.workflow and self.workflow.pk:
            existing_stages = WorkflowStage.objects.filter(
                workflow=self.workflow, 
                tenant=self.tenant
            ).exclude(pk=self.pk).values_list('sequence', flat=True)

            if existing_stages:
                max_seq = max(existing_stages)
                if self.sequence > max_seq + 1:
                    raise ValidationError(
                        f"Sequence is not consecutive. The next sequence should be {max_seq + 1}."
                    )
        else:
            # Logic for brand new Workflow records (Optional)
            # You can't easily check 'existing_stages' here because they aren't saved yet.
            # Usually, it's safe to let the first save happen, then validate on updates.
            pass
    def cleanv1(self):
        super().clean()
        if self.sequence < 1:
            raise ValidationError("Sequence must start from 1.")
        
        # Check for gaps in sequence within the same workflow
        existing_stages = WorkflowStage.objects.filter(
            workflow=self.workflow, 
            tenant=self.tenant
        ).exclude(pk=self.pk).values_list('sequence', flat=True)

        if existing_stages:
            max_seq = max(existing_stages)
            if self.sequence > max_seq + 1:
                raise ValidationError(f"Sequence is not consecutive. The next sequence should be {max_seq + 1}.")
        
        
        # earlier_final_stage = WorkflowStage.objects.filter(
        #     workflow=self.workflow,
        #     sequence__lt=self.sequence,
        #     is_final_stage=True,
        #     tenant=self.tenant
        # ).exists()

        # if earlier_final_stage:
        #     raise ValidationError(
        #         f"Cannot create stage {self.sequence}. A previous stage is already marked as the final stage."
        #     )
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        
    
    def __str__(self):
        return (
            f"{self.workflow.name} - Stage {self.sequence}: "
        )

STATUS_CHOICES =[
        ("pending", "Pending"), 
        ("rejected_for_amendment", "Rejected for Amendment"), 
        ("closed", "Approved"), 
        ("rejected", "Rejected")]
class WorkflowInstance(TenantModel):
    """A live instance of a workflow (e.g., John Doe's Leave Request #402)"""

    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, help_text="")
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()  # ID of the LeaveRequest or Expense
    target = GenericForeignKey("content_type", "object_id")
    current_stage = models.ForeignKey(WorkflowStage, on_delete=models.PROTECT)
    initiated_by = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="initiated_workflows"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    closure_ref = models.CharField(
        max_length=100, unique=True, blank=True, null=True, editable=False
    )
 

    def save(self, *args, **kwargs):
        # Apply the unique reference logic from your project
        if not self.closure_ref and self.completed_at:
            date_str = timezone.now().strftime("%Y%m%d")
            rand_suffix = str(random.randint(1000, 9999))
            self.closure_ref = f"{self.workflow.code.upper()}/{date_str}/{rand_suffix}"
            # self.closure_ref = f"/{date_str}/{rand_suffix}"
        super().save(*args, **kwargs)

    def track_history(self, actor, description, is_approved=None):
        """Narrative history log inspired by your previous project."""
        return HistoricalRecord.objects.create(
            tenant=self.tenant,
            instance=self,  # Linked to this workflow
            actor=actor,
            action_description=description,
            is_closed=is_approved,
        )
    # Inside class WorkflowInstance(TenantModel):

    # Inside class WorkflowInstance

  
    def move_to_next_stage(self):
        try:
            next_stage = WorkflowStage.objects.filter(
                workflow=self.workflow,
                sequence__gt=self.current_stage.sequence
            ).order_by('sequence').first()

            if not next_stage:
                return self.complete(actor=None)

            next_approvers = self.get_approver_for_stage(next_stage)
            
            # If the initiator is the approver, skip and notify
            if self.initiated_by in next_approvers:
                self.send_auto_approval_email(next_stage) # NEW
                self.track_history(None, f"System: Auto-approved stage {next_stage.sequence} (Requester is Approver).")
                
                self.current_stage = next_stage
                self.save()
                return self.move_to_next_stage() 

            self.current_stage = next_stage
            self.save()
            
        except Exception as e:
            logger.error(f"Error in move_to_next_stage: {e}", exc_info=True)

    def send_auto_approval_email(self, stage):
        """Sends a notification to the user that their request skipped a level."""
        subject = f"Auto-Approved: {self.workflow.name} - Stage {stage.sequence}"
        message = f"Your request {self.approval_ref} has been auto-approved at the '{stage.approver_type.name}' level because you are the designated approver."
        # send_mail(subject, message, 'hr@company.com', [self.initiated_by.employee_email])
    def get_approver_for_stage(self, stage, level_offset=0):
        """
        Logic 2b: Stage 3 -> Manager, Stage 5 -> Manager's Manager.
        """
        # 1. Direct Role Check
        if stage.approver_type and stage.approver_type.job_role and level_offset == 0:
            holders = Employee.objects.filter(grade__roles=stage.approver_type.job_role, tenant=self.tenant)
            if holders.exists(): return holders

        # 2. Sequential Hierarchy (Stage 1=Mgr, Stage 2=Grand-Mgr, etc.)
        target = self.initiated_by.line_manager
        # We climb up based on (sequence + offset)
        depth = stage.sequence + level_offset
        
        for _ in range(1, depth):
            if target and target.line_manager:
                target = target.line_manager
            else:
                break # CEO level reached
                
        return Employee.objects.filter(id=target.id) if target else Employee.objects.filter(is_hr_admin=True)
    
    
    @transaction.atomic
    def escalate_to_next_manager(self):
        """
        System-forced move up the chain due to turnaround_time breach.
        """
        try:
            # We look for the manager 1 level above the current sequence
            higher_approvers = self.get_approver_for_stage(self.current_stage, level_offset=1)
            
            approver_names = ", ".join([e.full_name for e in higher_approvers])
            
            # Log the escalation in history
            self.track_history(
                actor=None, 
                description=f"AUTO-ESCALATED: Responsibility shifted to {approver_names} due to SLA breach."
            )
            
            # If you have a 'current_assignee' field on the instance, update it here:
            # self.current_assignee = higher_approvers.first() 
            # self.save()

            log_with_context(logging.WARNING, f"Instance {self.approval_ref} escalated to {approver_names}", None)
            
        except Exception as e:
            logger.error(f"Escalation failed for Workflow {self.id}: {e}", exc_info=True)

    @transaction.atomic
    def complete(self, actor):
        """
        Generic completion logic that works for ANY model.
        """
        self.status = "APPROVED"
        self.completed_at = timezone.now()
        self.save()

        # Check if the target model has a custom finalization method
        # This makes it robust for Leave, Payroll, etc.

        # This is where we use the state name you requested
        if hasattr(self.target, "status"):
            self.target.status = "leave_application"
            
        if hasattr(self.target, "finalize_workflow"):
            try:
                self.target.finalize_workflow(actor)
                log_with_context(logging.INFO, f"Workflow {self.approval_ref} finalized by target logic.", actor.user)
            except Exception as e:
                logger.error(f"Finalization failed for {self.target}: {e}", exc_info=True)
                raise  # Rollback transaction if business logic fails
        
        self.track_history(actor, "Workflow completed successfully.", is_approved=True)
        logger.info(f"WorkflowInstance {self.id} completed by {actor.full_name}")

    @property
    def get_progress_data(self):
        stages = self.workflow.stages.all()
        history = self.actions.all()

        nodes = []
        for stage in stages:
            status = "pending"
            actor_name = stage.approver_type.name

            # Check if this stage was already completed
            action = history.filter(step=stage).first()
            if action:
                status = "completed" if action.action == "APP" else "rejected"
                actor_name = action.actor.full_name

            nodes.append(
                {
                    "name": stage.approver_type.name,
                    "status": status,
                    "actor": actor_name,
                    "is_current": (self.current_stage == stage),
                }
            )
        return nodes



    def __str__(self):
        return f"{self.workflow.name} for {self.target}"

    def get_approver_for_stagev1(self, stage, level_offset=0):
        """
        Calculates approver based on Stage Sequence + Offset.
        level_offset=0: Current intended approver.
        level_offset=1: The current approver's manager (Escalation).
        """
        # 1. If a specific Job Role is defined, try that first
        if stage.approver_type and stage.approver_type.job_role and level_offset == 0:
            holders = Employee.objects.filter(
                grade__roles=stage.approver_type.job_role,
                tenant=self.tenant,
                is_active=True
            )
            if holders.exists():
                return holders

        # 2. Hierarchy Logic: Start with the initiator's manager
        # Base depth is the stage sequence + any escalation offset
        depth = stage.sequence + level_offset
        
        target_approver = self.initiated_by.line_manager
        last_valid = target_approver

        for _ in range(1, depth):
            if target_approver and target_approver.line_manager:
                target_approver = target_approver.line_manager
                last_valid = target_approver
            else:
                # We hit the top of the Org Chart (e.g., CEO)
                target_approver = last_valid
                break

        if target_approver:
            return Employee.objects.filter(id=target_approver.id)

        # 3. Ultimate Fallback: HR Admin
        return Employee.objects.filter(is_hr_admin=True, tenant=self.tenant)
    def move_to_next_stagev1(self):
        """
        Finds the next stage, skipping if the initiator is the approver.
        """
        try:
            log_with_context(logging.INFO, f"Skipping Stage {next_stage.user.full_name}: Requester is approver.", None)
            next_stage = WorkflowStage.objects.filter(
                workflow=self.workflow,
                sequence__gt=self.current_stage.sequence
            ).order_by('sequence').first()
            log_with_context(logging.INFO, f"Skipping Stage {next_stage.sequence}: Requester is approver.", None)
            if not next_stage:
                return self.complete(actor=None) # Final Stage reached

            # Logic 2a: Check if Requester is the Approver for the next stage
            next_approvers = self.get_approver_for_stage(next_stage)
            if self.initiated_by in next_approvers:
                log_with_context(logging.INFO, f"Skipping Stage {next_stage.sequence}: Requester is approver.", None)
                self.current_stage = next_stage
                self.save()
                return self.move_to_next_stage() # Recursively check the next one

            self.current_stage = next_stage
            self.save()
            
        except Exception as e:
            logger.error(f"Error moving to next stage: {e}", exc_info=True)
    # Inside WorkflowInstance



class HistoricalRecord(TenantModel):
    instance = models.ForeignKey(
        WorkflowInstance, on_delete=models.CASCADE, related_name="history"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    actor = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    action_description = models.TextField()
    is_closed = models.BooleanField(
        null=True,
        blank=True,
        help_text="True if action was an closed, False if rejection, None otherwise",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.instance.workflow.name} - {self.action_description[:30]}"


