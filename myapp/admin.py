# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin


from .models import (Comment, CustomUser, Order, OrderItem, Package,
                     ServiceCategory,Tenant, TenantAttribute, Workflow, WorkflowStage, WorkflowInstance, WorkflowHistory,
                     ServiceChoices,PremiumClient,QR,DeliveryPricing, Color,Cluster, State, Town)

from .landing_models import (
    LandingCarousel, LandingText, LandingValue, LandingCommitment, 
    LandingPricingCard, LandingCustomerStory, LandingFAQ
)
class CustomUserAdmin(UserAdmin):
    """
    Customizes the Django admin to manage the CustomUser model.
    """
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('phone_number', 'address')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('phone_number', 'address')}),
    )
    list_display = ('email', 'phone_number', 'address', 'is_staff')
    search_fields = ('email', 'phone_number', 'address')
    ordering = ('email',)

class ServiceCategoryAdmin(admin.ModelAdmin):
    """
    Admin configuration for the ServiceCategory model.
    """
    list_display = ('name',)
    search_fields = ('name',)

class PackageAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Package model.fpackage
    
    """
    list_display = ('id', 'category', 'service_type', 'price', 'delivery_time_days', 'tenant')
    list_filter = ('category', 'service_type')
    search_fields = ('category__name', 'service_type')

class OrderItemInline(admin.TabularInline):
    """
    Allows OrderItems to be edited directly within the Order admin page.
    """
    model = OrderItem
    extra = 0
    fields = ('package', 'name', 'color',"qr_code","qr_initiator")
    readonly_fields = ('color',)

class OrderAdmin(admin.ModelAdmin):
    """
    Customizes the Django admin to manage the Order model.
    """
    list_display = (
        'id', 'status','order_code', 'created_at', 'total_price',
        'estimated_delivery_date',"work_initiator",
    )
    list_filter = ('status', 'created_at')
    search_fields = ('id', 'user__email', 'customer_name', 'customer_phone')
    inlines = [OrderItemInline]
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Order Information', {
            'fields': ( 'status', 'order_code','total_price', 'estimated_delivery_date',  'has_confirmation_received', 'work_initiator',"state")
        }),
        ('Customer Details', {
            'fields': ('customer_name', 'customer_phone', 'customer_email', 'address', 'pickup_date', 'special_instructions')
        }),
    )

class CommentAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Comment model.
    """
    list_display = ('order', 'body', 'created_at', 'is_approved')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('order__id', 'body')
    actions = ['approve_comments']
    
    def approve_comments(self, request, queryset):
        """
        Action to approve selected comments.
        """
        queryset.update(is_approved=True)
        self.message_user(request, "Selected comments have been approved.")
    approve_comments.short_description = "Approve selected comments"


from django.contrib.auth import get_user_model

User = get_user_model()
# admin.site.unregister(User)
# admin.site.register(User, CustomUserAdmin)
# Register your models with the admin site
# admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(ServiceCategory, ServiceCategoryAdmin)
admin.site.register(Package, PackageAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.site_header = "Laundry Service Admin"
admin.site.site_title = "Laundry Service Admin Portal"
admin.site.index_title = "Welcome to the Laundry Service Admin Portal"
admin.site.register(CustomUser)
admin.site.register(WorkflowHistory)
admin.site.register(ServiceChoices)
admin.site.register(Color)

class TenantAttributeInline(admin.StackedInline):
    model = TenantAttribute
    can_delete = False

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    inlines = [TenantAttributeInline]
    list_display = ('name', 'code', 'subdomain', 'is_active', 'created_at')

@admin.register(Cluster)
class ClusterAdmin(admin.ModelAdmin):
    filter_horizontal = ('towns',)
    list_display = ('name', 'tenant')

admin.site.register(State)
admin.site.register(Town)
admin.site.register(PremiumClient, admin.ModelAdmin)
admin.site.register(QR)
admin.site.register(DeliveryPricing)





admin.site.register(LandingCarousel)
admin.site.register(LandingText)
admin.site.register(LandingValue)
admin.site.register(LandingCommitment)
admin.site.register(LandingPricingCard)
admin.site.register(LandingCustomerStory)
admin.site.register(LandingFAQ)

class WorkflowStepInline(admin.TabularInline):
    model = WorkflowStage
    extra = 1
@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = ("name",)
    inlines = [WorkflowStepInline]






@admin.register(WorkflowInstance)
class WorkflowInstanceAdmin(admin.ModelAdmin):

    list_display = ("id", "workflow", "object_id", "content_type", "target", "created_at", "current_stage")
    # inlines = [WorkflowStageInstanceInline]

    @admin.display(description="Target Object")
    def target_info(self, obj):
        return f"{obj.content_type} (ID: {obj.object_id})"

    @admin.display(description="Workflow Stages")
    def stages(self, obj): 
        return ", ".join([f"Stage {s.sequence}" for s in obj.workflow.stages.all()]) 
    readonly_fields = ("stages",)


