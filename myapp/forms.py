from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser, Order, OrderItem, Comment, ServiceCategory, Service
class CustomUserCreationForm(UserCreationForm):
    """
    A form that creates a user, with no username, but with email, phone number, and address.
    """
    class Meta:
        model = CustomUser
        fields = ('email', 'phone_number', 'address',)
class CustomUserChangeForm(UserChangeForm):
    """
    A form for updating a user.
    """
    class Meta:
        model = CustomUser
        fields = ('email', 'phone_number', 'address',)
class OrderForm(forms.ModelForm):
    """
    Form for customers to place a new order.
    """
    class Meta:
        model = Order
        fields = [
            'customer_name', 'customer_email', 'customer_phone', 'address',
            'pickup_date', 'special_instructions'
        ]
        widgets = {
            'pickup_date': forms.DateInput(attrs={'type': 'date'}),
        }
class OrderItemForm(forms.ModelForm):
    """
    Form for adding a single item to an order.
    """
    class Meta:
        model = OrderItem
        fields = ['name', 'color']

class AddItemForm(forms.Form):
    """
    Form for adding an item with service selection for HTMX requests.
    """
    name = forms.CharField(max_length=100, required=True)
    color = forms.CharField(max_length=50, required=False)
    category = forms.ModelChoiceField(queryset=ServiceCategory.objects.all(), required=True)
    service = forms.ModelChoiceField(queryset=Service.objects.none(), required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'category' in self.data:
            try:
                category_id = int(self.data.get('category'))
                self.fields['service'].queryset = Service.objects.filter(category_id=category_id).order_by('service_type')
            except (ValueError, TypeError):
                pass  # invalid input from the client
class CommentForm(forms.ModelForm):
    """
    Form for a customer to add a comment to their order.
    """
    class Meta:
        model = Comment
        fields = ['body']
class ServiceSelectionForm(forms.Form):
    """
    Form to select a category and service for HTMX requests.
    """
    category = forms.ModelChoiceField(queryset=ServiceCategory.objects.all(), required=True)
    service = forms.ModelChoiceField(queryset=Service.objects.none(), required=True)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'category' in self.data:
            try:
                category_id = int(self.data.get('category'))
                self.fields['service'].queryset = Service.objects.filter(category_id=category_id).order_by('service_type')
            except (ValueError, TypeError):
                pass  # invalid input from the client
