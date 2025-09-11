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


# POST AJADI
from django import forms
from .models import LaundryItem

from django import forms
from .models import LaundryItem

class LaundryItemForm1(forms.ModelForm):
    class Meta:
        model = LaundryItem
        fields = ['service', 'name', 'color']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={'class': 'form-control'}),
            'service': forms.Select(attrs={'class': 'form-select'}),
        }




from django import forms
from .models import LaundryItem, ServiceType, CustomerRequest, Service

class LaundryItemForm(forms.ModelForm):
    class Meta:
        model = LaundryItem
        fields = ['service', 'name', 'color']
        widgets = {
            'service': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={'class': 'form-control'}),
        }

    # Add a category field to the form for HTMX dynamic rendering
    category = forms.ModelChoiceField(
        queryset=Service.objects.values_list('category', flat=True).distinct(),
        empty_label="---------",
        label="Category",
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'service' in self.initial:
            category_id = self.initial['service'].category.id
            self.fields['category'].initial = category_id
            self.fields['service'].queryset = Service.objects.filter(category_id=category_id)

class CommentForm(forms.Form):
    """
    A simple form for a customer to submit a comment or question about their order.
    """
    comment = forms.CharField(
        label="Your Comment",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        required=True
    )
