# Register your models here.
from myapp.models import Feeder
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.utils.safestring import mark_safe


from .models import (Comment, CustomUser, Order, OrderItem, Package,
                     ServiceCategory,Tenant, TenantAttribute, Workflow, WorkflowStage, WorkflowInstance, WorkflowHistory,
                     ServiceChoices,PremiumClient,QR,DeliveryPricing, Color,Cluster, State, Town,Feeder,PowerStatus,School_tenant,Student_profile,Attendance_log)

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

@admin.register(Feeder)
class FeederAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'band',
        'live_status_badge',
        'transformer_name',
        'transformer_code',
        'registered_phone',
        'sim_serial',
        'whatsapp_primary',
        'whatsapp_group',
        'view_logs_link',
        'created_at',
    )
    list_filter = ('band', 'created_at')
    search_fields = (
        'name',
        'transformer_name',
        'transformer_code',
        'registered_phone',
        'msisdn',
        'custodian_name',
        'custodian_phone',
        'sim_serial',
        'whatsapp_primary',
        'whatsapp_group',
    )
    ordering = ('name',)
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Feeder Information', {
            'fields': ('name', 'band', 'created_at')
        }),
        ('Transformer & Hardware', {
            'fields': ('transformer_name', 'transformer_code', 'registered_phone', 'msisdn', 'sim_serial')
        }),
        ('Custodian Info', {
            'fields': ('custodian_name', 'custodian_phone')
        }),
        ('WhatsApp Alerts & Notification Recipients', {
            'fields': ('whatsapp_primary', 'whatsapp_group', 'primary_recipient'),
            'description': 'Comma-separated WhatsApp phone numbers (with country code, e.g. 23480...) and group JIDs (e.g. 1203...@g.us).'
        }),
    )

    @admin.display(description="Live Status")
    def live_status_badge(self, obj):
        latest = obj.updates.order_by('-server_time').first()
        if not latest:
            return mark_safe('<span style="color: #9ca3af; font-size: 11px;">No Data</span>')
        s = (latest.status or "").upper()
        if s == "ON":
            bg = "#d1fae5"
            color = "#065f46"
            icon = "🟢"
        elif s == "OFF":
            bg = "#fee2e2"
            color = "#991b1b"
            icon = "🔴"
        else:
            bg = "#fef3c7"
            color = "#92400e"
            icon = "🟡"
        time_str = latest.server_time.strftime("%H:%M:%S") if latest.server_time else ""
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 3px 8px; border-radius: 9999px; font-weight: 600; font-size: 11px;" title="Last update: {}">{} {}</span>',
            bg, color, time_str, icon, s
        )

    @admin.display(description="Power Logs")
    def view_logs_link(self, obj):
        from django.urls import reverse
        url = reverse("admin:myapp_powerstatus_changelist") + f"?feeder__id__exact={obj.id}"
        return format_html('<a class="button" style="padding: 2px 8px; font-size: 11px;" href="{}">⚡ View Logs</a>', url)


@admin.register(PowerStatus)
class PowerStatusAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'event_id_display',
        'feeder',
        'status_badge',
        'whatsapp_status_badge',
        'three_phase_display',
        'peak_a0',
        'dt_display',
        'server_time',
        'timestamp',
    )
    list_filter = (
        'status',
        'whatsapp_status',
        'dt',
        'feeder',
        ('server_time', admin.DateFieldListFilter),
    )
    date_hierarchy = 'server_time'
    search_fields = (
        'event_id',
        'feeder__name',
        'feeder__transformer_name',
        'feeder__transformer_code',
        'status',
        'sim_serial',
        'msisdn',
        'dt',
    )
    ordering = ('-server_time',)
    list_select_related = ('feeder',)
    list_per_page = 50
    readonly_fields = (
        'event_id',
        # 'feeder',
        # 'status',
        # 'whatsapp_status',
        # 'timestamp',
        # 'server_time',
        # 'peak_a0',
        # 'sim_serial',
        # 'msisdn',
        # 'dt',
        # 'volt_r',
        # 'stat_r',
        # 'volt_y',
        # 'stat_y',
        # 'volt_b',
        # 'stat_b',
    )
    fieldsets = (
        ('Event Information', {
            'fields': ('event_id', 'feeder', 'status', 'whatsapp_status')
        }),
        ('Telemetry & Device Info', {
            'fields': ('server_time', 'timestamp', 'dt', 'peak_a0', 'sim_serial', 'msisdn')
        }),
        ('Three-Phase Telemetry (PEARL DT)', {
            'fields': (
                ('stat_r', 'volt_r'),
                ('stat_y', 'volt_y'),
                ('stat_b', 'volt_b'),
            )
        }),
    )

    @admin.display(description="Event ID", ordering="event_id")
    def event_id_display(self, obj):
        if not obj.event_id:
            return "-"
        full_uuid = str(obj.event_id)
        short_uuid = full_uuid[:8] + "..."
        return format_html('<code title="{}" style="font-size: 11px; cursor: pointer;">{}</code>', full_uuid, short_uuid)

    @admin.display(description="Power Status", ordering="status")
    def status_badge(self, obj):
        s = (obj.status or "").upper()
        if s == "ON":
            bg = "#d1fae5"
            color = "#065f46"
            icon = "🟢"
        elif s == "OFF":
            bg = "#fee2e2"
            color = "#991b1b"
            icon = "🔴"
        else:
            bg = "#fef3c7"
            color = "#92400e"
            icon = "🟡"
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 3px 8px; border-radius: 9999px; font-weight: 600; font-size: 11px;">{} {}</span>',
            bg, color, icon, s
        )

    @admin.display(description="WhatsApp Status", ordering="whatsapp_status")
    def whatsapp_status_badge(self, obj):
        ws = (obj.whatsapp_status or "undelivered").lower()
        if ws == "delivered":
            bg = "#d1fae5"
            color = "#047857"
            icon = "✓"
        else:
            bg = "#ffedd5"
            color = "#c2410c"
            icon = "⏳"
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 3px 8px; border-radius: 9999px; font-weight: 600; font-size: 11px;">{} {}</span>',
            bg, color, icon, ws.capitalize()
        )

    @admin.display(description="Three-Phase Telemetry")
    def three_phase_display(self, obj):
        if not obj.is_three_phase:
            return mark_safe('<span style="color: #9ca3af; font-size: 11px;">1-Phase</span>')
        return format_html(
            '<span style="font-size: 11px; font-family: monospace;">'
            '<strong style="color: #dc2626;">R:</strong>{:.0f}V ({}) '
            '<strong style="color: #d97706;">Y:</strong>{:.0f}V ({}) '
            '<strong style="color: #2563eb;">B:</strong>{:.0f}V ({})'
            '</span>',
            obj.volt_r, obj.stat_r or "-",
            obj.volt_y, obj.stat_y or "-",
            obj.volt_b, obj.stat_b or "-"
        )

    @admin.display(description="Device", ordering="dt")
    def dt_display(self, obj):
        return obj.dt or "Standard"
 



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



@admin.register(School_tenant)
class School_tenantAdmin(admin.ModelAdmin):
    list_display = ("id", "tenant_name", "tenant_code", "evolution_instance", "evolution_api")
    search_fields = ("tenant_name", "tenant_code")
    ordering = ("tenant_name",)

@admin.register(Attendance_log)
class Attendance_logAdmin(admin.ModelAdmin):
    list_display = ("id", "student", "status", "created")
    list_filter = ("status", "created")
    search_fields = ("student__student_firstname", "student__student_lastname", "student__student_id")
    ordering = ("-created",)

@admin.register(Student_profile)
class Student_profileAdmin(admin.ModelAdmin):
    list_display = ("id", "tenant_name", "student_firstname", "student_lastname", "student_id", "student_email", "phone_number")
    list_filter = ("tenant_name", "created")
    search_fields = ("student_firstname", "student_lastname", "student_id", "student_email")
    ordering = ("student_lastname", "student_firstname")