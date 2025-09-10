from django import forms
from .models import CustomerRequest, LaundryItem, CustomUser

class ServiceRequestForm(forms.ModelForm):
    class Meta:
        model = CustomerRequest
        fields = ['address', 'contact_number']

class AdminItemForm(forms.ModelForm):
    class Meta:
        model = LaundryItem
        fields = ['name', 'service_type', 'price', 'delivery_time_days']

class CustomUserCreationForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'phone_number', 'address']