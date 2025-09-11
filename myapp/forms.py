from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Order, OrderItem, Comment, CustomUser

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['customer_name', 'customer_email', 'customer_phone', 'address', 'pickup_date', 'special_instructions']
        widgets = {
            'pickup_date': forms.DateInput(attrs={'type': 'date'}),
        }

class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['service', 'name', 'color']

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


