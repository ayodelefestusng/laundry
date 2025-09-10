from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, CustomerRequest,LaundryItem,WorkflowHistory

# class CustomUserAdmin(UserAdmin):
#     model = CustomUser
#     list_display = ['username', 'email', 'phone_number', 'is_staff']
#     fieldsets = UserAdmin.fieldsets + (
#         (None, {'fields': ('phone_number', 'address', 'is_staff', 'is_customer')}),
#     )

# admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(CustomUser)
admin.site.register(CustomerRequest)
admin.site.register(LaundryItem)
admin.site.register(WorkflowHistory)