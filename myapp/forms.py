from django import forms
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.forms import widgets

from .models import (Comment, CustomUser, Order, OrderItem, Package, Payment,Package, ServiceCategory
                     )


class CustomUserCreationForm(UserCreationForm):
    """
    A form that creates a user, with no username, but with email, phone number, and address.
    """
    class Meta:
        model = CustomUser
        fields = ('email', 'name',)


from django.urls import reverse_lazy
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, HTML, Field
from django.contrib.auth.forms import SetPasswordForm
class RegistrationForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ["email", "name" ]
        widgets = {
            'email': forms.EmailInput(attrs={
                'hx-post': reverse_lazy('laundry:check_username'),
                'hx-trigger': 'keyup',
                'hx-target': '#username-err'
            }),
        }


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse_lazy('laundry:register')
        self.helper.form_method = ('POST')
        self.helper.add_input(Submit('submit', 'Register'))
        self.helper.layout = Layout(
        
            Field('email'),
            # This is the custom div with id "ayo"
            HTML('<div class="text-danger mt-2" id="username-err"></div>'),
             HTML('<div class="custom-divider"></div>'),
             HTML('<p></p>'),
            Field('name'),
        )

    
    def clean_email(self):
        email = self.cleaned_data.get("email")
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email


class PasswordSetupForm(SetPasswordForm):
    pass

        
class PasswordChangeForm(forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput)
    new_password = forms.CharField(widget=forms.PasswordInput)

from django.contrib.auth.forms import PasswordResetForm 
from django.utils.translation import gettext_lazy as _
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.template import loader
from django.core.mail import EmailMultiAlternatives
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings
from django.contrib.auth import get_user_model
import logging
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.template import loader
from django.core.mail import EmailMultiAlternatives
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings
from django.contrib.auth import get_user_model
import logging
from django.utils.encoding import force_bytes
logger = logging.getLogger(__name__)

UserModel = get_user_model()



# class CustomUserCreationForm1(UserCreationForm):
#     """
#     A form that creates a user, with no username, but with email, phone number, and address.
#     """
#     class Meta:
#         model = CustomUser
#         fields = ('email', 'phone_number', 'address',)
class CustomUserChangeForm(UserChangeForm):
    """
    A form for updating a user.
    """
    class Meta:
        model = CustomUser
        fields = ('email', 'phone', 'name',)
from django import forms
from datetime import datetime, timedelta

class OrderForm(forms.ModelForm):
    
    class Meta:
        model = Order
        fields = [
            'customer_name', 'customer_email', 'customer_phone', 'address',
            'pickup_date', 'special_instructions'
        ]
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'hx-get': '/customer/check_email/',
                'hx-trigger': 'keyup changed delay:500ms',
                'hx-target': '#email-error'
            }),
            'customer_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'cols': 40}),
            'pickup_date': forms.DateTimeInput(
                attrs={'class': 'form-control', 'id': 'pickup-calendar',}
            ),
               'special_instructions': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 2,
                    'cols': 40,
                    'placeholder': 'I want it specially washed'
                }
            ),

        }
        labels = {
            'customer_name': 'Customer Name',
            'customer_email': 'Customer Email',
            'customer_phone': 'Customer Phone',
            'address': 'Address',
            'pickup_date': 'Pickup Date',
            'special_instructions': 'Special Instructions',
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make all fields required except special_instructions
        for field_name in self.fields:
            if field_name != 'special_instructions':
                self.fields[field_name].required = True
            else:
                self.fields[field_name].required = False



class OrderFormv1(forms.ModelForm):
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
            # 'pickup_date': forms.DateInput(attrs={'type': 'date'}),
             'pickup_date': forms.DateInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
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
    package = forms.ModelChoiceField(queryset=Package.objects.none(), required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'category' in self.data:
            try:
                category_id = int(self.data.get('category'))
                self.fields['package'].queryset = Package.objects.filter(category_id=category_id).order_by('service_type')
            except (ValueError, TypeError):
                pass  # invalid input from the client
class CommentForm(forms.ModelForm):
    """
    Form for a customer to add a comment to their order.
    """
    class Meta:
        model = Comment
        fields = ['body']
        widgets = { 'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'cols': 40}),}
        labels = {'body': 'Comment',}
class ServiceSelectionForm(forms.Form):
    """
    Form to select a category and service for HTMX requests.
    """
    category = forms.ModelChoiceField(queryset=ServiceCategory.objects.all(), required=True)
    service = forms.ModelChoiceField(queryset=Package.objects.none(), required=True)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'category' in self.data:
            try:
                category_id = int(self.data.get('category'))
                self.fields['service'].queryset = Service.objects.filter(category_id=category_id).order_by('service_type')
            except (ValueError, TypeError):
                pass  # invalid input from the client
