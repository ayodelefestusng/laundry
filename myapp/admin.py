from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import CustomUser, ServiceCategory, ServiceType, Service, Order, OrderItem, Comment

# Unregister the default User model
# admin.site.unregister(User)

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

class ServiceCategoryAdmin(admin.ModelAdmin):
    """
    Admin configuration for the ServiceCategory model.
    """
    list_display = ('name',)
    search_fields = ('name',)

class ServiceTypeAdmin(admin.ModelAdmin):
    """
    Admin configuration for the ServiceType model.
    """
    list_display = ('name',)
    search_fields = ('name',)

class ServiceAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Service model.
    """
    list_display = ('name', 'category', 'service_type', 'price', 'delivery_time_days')
    list_filter = ('category', 'service_type')
    search_fields = ('name',)

class OrderItemInline(admin.TabularInline):
    """
    Allows OrderItems to be edited directly within the Order admin page.
    """
    model = OrderItem
    extra = 0
    fields = ('service', 'name', 'color', 'price', 'delivery_time_days')
    readonly_fields = ('price', 'delivery_time_days')

class OrderAdmin(admin.ModelAdmin):
    """
    Customizes the Django admin to manage the Order model.
    """
    list_display = (
        'id', 'user', 'status', 'created_at', 'total_price',
        'estimated_delivery_date'
    )
    list_filter = ('status', 'created_at')
    search_fields = ('id', 'user__username', 'customer_name', 'customer_phone')
    inlines = [OrderItemInline]
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Order Information', {
            'fields': ('user', 'status', 'created_at', 'total_price', 'estimated_delivery_date', 'notes')
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


# Register your models with the admin site
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(ServiceCategory, ServiceCategoryAdmin)
admin.site.register(ServiceType, ServiceTypeAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Comment, CommentAdmin)
