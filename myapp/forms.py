from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Order, OrderItem, Comment, CustomUser, Service, ServiceCategory

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['customer_name', 'customer_email', 'customer_phone', 'address', 'pickup_date', 'special_instructions']
        widgets = {
            'pickup_date': forms.DateInput(attrs={'type': 'date'}),
        }

class OrderItemForm(forms.ModelForm):
    """
    A form for adding or editing an item within a laundry order.
    This form is designed to work with the HTMX-driven cascading dropdowns.
    """
    # This field is used for filtering in the template, but not saved to the model.
    category = forms.ModelChoiceField(
        queryset=ServiceCategory.objects.all(),
        required=False,
        label="Category"
    )

    class Meta:
        model = OrderItem
        fields = ['category', 'service', 'name', 'color']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'E.g., Shirt, Pants'}),
            'color': forms.TextInput(attrs={'placeholder': 'E.g., Blue, White'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Check for initial data from a GET request (e.g., in the edit form)
        if 'category' in self.initial:
            category_id = self.initial['category']
        # Check for data from a POST request (e.g., form submission)
        elif 'category' in self.data:
            category_id = self.data.get('category')
        else:
            category_id = None
        
        # Filter the service queryset based on the selected category
        if category_id:
            self.fields['service'].queryset = Service.objects.filter(category_id=category_id)
        else:
            self.fields['service'].queryset = Service.objects.none()

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['body']

class CustomUserCreationForm(UserCreationForm):
    """
    A custom form for creating a new user with extra fields.
    This form inherits from Django's UserCreationForm for secure password handling.
    """
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = UserCreationForm.Meta.fields + ('email', 'phone_number', 'address')



class ServiceForm(forms.ModelForm):
    """
    A form for creating and updating Service objects.
    """
    class Meta:
        model = Service
        fields = ['price', 'delivery_time_days', 'category', 'service_type']
