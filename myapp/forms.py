from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomerRequest, LaundryItem, CustomUser, Service

class ServiceRequestForm(forms.ModelForm):
    """
    Form for customers to submit a new laundry service request.
    """
    class Meta:
        model = CustomerRequest
        fields = ['address', 'contact_number']


# myapp/forms.py

from django import forms
from .models import LaundryItem, Service, Category
from django.forms import ModelChoiceField

class AdminItemForm(forms.ModelForm):
    # Add a category field for the cascading dropdown
    category = forms.ModelChoiceField(queryset=Category.objects.all(), label="Category")
    
    # The service field is initially empty and will be populated by HTMX
    service = forms.ModelChoiceField(
        queryset=Service.objects.none(),  # Initially no services
        label="Service Type"
    )

    class Meta:
        model = LaundryItem
        fields = ['category', 'service', 'name', 'color']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # This will handle editing existing forms correctly
        if self.instance and self.instance.pk and self.instance.service:
            # Set the initial category from the existing service
            self.fields['category'].initial = self.instance.service.category
            # Populate the service field with services for the correct category
            self.fields['service'].queryset = self.instance.service.category.services.all()



class AdminItemForm1(forms.ModelForm):
    """
    Form for admins to add or edit a single laundry item.
    The service field is a dropdown populated from the Service model.
    """
    service = forms.ModelChoiceField(queryset=Service.objects.all(), label="Service & Category")
    
    class Meta:
        model = LaundryItem
        fields = ['name', 'service', 'color']

class CustomUserCreationForm(UserCreationForm):
    """
    A custom form for creating a new user with extra fields.
    This form inherits from Django's UserCreationForm for secure password handling.
    """
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = UserCreationForm.Meta.fields + ('email', 'phone_number', 'address')