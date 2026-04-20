from django import forms
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.forms import widgets

from .models import (Comment, CustomUser, Order, OrderItem, Package, Payment, Package, ServiceCategory, Color
                     )


from django.urls import reverse_lazy
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, HTML, Field
from django.contrib.auth.forms import SetPasswordForm
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
from django import forms
from datetime import datetime, timedelta
class CustomUserCreationForm(UserCreationForm):
    """
    A form that creates a user, with no username, but with email, phone number, and address.
    """
    class Meta:
        model = CustomUser
        fields = ('email', 'name',)

from django.contrib.auth.forms import AuthenticationForm

class CustomAuthenticationForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise forms.ValidationError(
                "Your account is inactive. Access denied.",
                code='inactive',
            )
        super().confirm_login_allowed(user)


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

from .models import Cluster, Town, State
class OrderForm(forms.ModelForm):
    
    class Meta:
        model = Order
        # fields = [
        #     'customer_name', 'customer_email', 'customer_phone', 'state', 'town', 'address', 'pickup_latitude', 'pickup_longitude',
        #     'delivery_option', 'recipient_name', 'recipient_email', 
        #     'recipient_phone', 'recipient_state', 'recipient_town', 'recipient_address', 'recipient_latitude', 'recipient_longitude',
        #     'pickup_date', 'special_instructions'
        # ]
        fields = [
            'customer_name', 'customer_email', 'customer_phone', 'state', 'town', 'address',
            'pickup_latitude', 'pickup_longitude', 'delivery_option',
            'recipient_name', 'recipient_email', 'recipient_phone',
            'recipient_state', 'recipient_town', 'recipient_address',
            'recipient_latitude', 'recipient_longitude',
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
            'state': forms.Select(attrs={
                'class': 'form-select select2', 
                'hx-get': reverse_lazy('laundry:htmx_get_towns'), 
                'hx-target': '#id_town', 
                'hx-trigger': 'change'
            }),
            'town': forms.Select(attrs={
                'class': 'form-select select2', 
                'id': 'id_town',
                'hx-get': reverse_lazy('laundry:htmx_calculate_deliverys'),
                'hx-target': '#delivery-price-display',
                'hx-trigger': 'change'
            }),
            'address': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_address', 'placeholder': 'Enter your pickup address'}),
            
            'delivery_option': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            
            'recipient_name': forms.TextInput(attrs={'class': 'form-control'}),
            'recipient_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'recipient_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'recipient_state': forms.Select(attrs={
                'class': 'form-select select2',
                'hx-get': reverse_lazy('laundry:htmx_get_towns'),
                'hx-target': '#id_recipient_town',
                'hx-trigger': 'change'
            }),
            'recipient_town': forms.Select(attrs={'class': 'form-select select2', 'id': 'id_recipient_town'}),
            'recipient_address': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_recipient_address', 'placeholder': 'Enter recipient address'}),
            'pickup_latitude': forms.HiddenInput(),
            'pickup_longitude': forms.HiddenInput(),
            'recipient_latitude': forms.HiddenInput(),
            'recipient_longitude': forms.HiddenInput(),
            
            'pickup_date': forms.DateTimeInput(
                attrs={'class': 'form-control', 'id': 'pickup-calendar', 'type': 'datetime-local'}
            ),
            'special_instructions': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 2,
                    'cols': 40,
                    'placeholder': 'Special care instructions...'
                }
            ),
        }
        labels = {
            'customer_name': 'Customer Name',
            'customer_email': 'Customer Email',
            'customer_phone': 'Customer Phone',
            'state': 'State',
            'town': 'Town',
            'address': 'Address',
            'recipient_state': 'Recipient State',
            'recipient_town': 'Recipient Town',
            'pickup_date': 'Pickup Date',
            'special_instructions': 'Special Instructions',
        }
        
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        tenant = kwargs.pop('tenant', None)  # pass tenant context when instantiating the form

        super().__init__(*args, **kwargs)

        
        # Restrict states/towns to those in clusters for this tenant
        if tenant:
            clusters = Cluster.objects.filter(tenant=tenant)
            towns_in_clusters = Town.objects.filter(clusters__in=clusters).distinct()
            states_in_clusters = State.objects.filter(towns__in=towns_in_clusters).distinct()

            self.fields['state'].queryset = states_in_clusters.order_by('name')
            self.fields['town'].queryset = towns_in_clusters.order_by('name')

            self.fields['recipient_state'].queryset = states_in_clusters.order_by('name')
            self.fields['recipient_town'].queryset = towns_in_clusters.order_by('name')
            
        # Auto-populate if user is in Customer group
        if user and user.is_authenticated:
            if user.groups.filter(name='Customer').exists():
                self.fields['customer_name'].initial = user.name
                self.fields['customer_email'].initial = user.email
                self.fields['customer_phone'].initial = user.phone
                self.fields['address'].initial = user.address
                self.fields['pickup_latitude'].initial = user.latitude
                self.fields['pickup_longitude'].initial = user.longitude

        # Make recipient and pickup coordinates optional by default
        optional_fields = [
            'recipient_name', 'recipient_email', 'recipient_phone', 
            'recipient_state', 'recipient_town', 'recipient_address', 
            'recipient_latitude', 'recipient_longitude',
            'pickup_latitude', 'pickup_longitude', 'delivery_option', 'special_instructions'
        ]
        for field in optional_fields:
            if field in self.fields:
                self.fields[field].required = False
        
        if 'delivery_option' in self.fields:
            self.fields['delivery_option'].initial = 'home_delivery'

        # Make all other fields required
        for field_name in self.fields:
            if field_name not in optional_fields:
                self.fields[field_name].required = True


class OrderItemForm(forms.ModelForm):
    """
    Form for editing an existing item.
    """
    color = forms.ChoiceField(
        choices=[],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select color-select-styled'})
    )
    quantity = forms.IntegerField(
        min_value=1, max_value=10,
        widget=forms.Select(
            choices=[(i, str(i)) for i in range(1, 11)],
            attrs={'class': 'form-select shadow-sm'}
        )
    )

    class Meta:
        model = OrderItem
        fields = ['package', 'name', 'color', 'color_custom', 'quantity']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'color_custom': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Describe color...',
            }),
        }

    def __init__(self, *args, **kwargs):
        # We need tenant context for color queryset
        tenant = None
        if 'instance' in kwargs and kwargs['instance']:
            tenant = kwargs['instance'].tenant
        
        super().__init__(*args, **kwargs)
        
        if tenant:
            color_choices = [('', 'Select color...')]
            color_choices += [(str(c.id), c.name) for c in Color.objects.filter(tenant=tenant)]
            color_choices.append(('other', 'Other / Custom...'))
            self.fields['color'].choices = color_choices
            
            # Initial value for color if instance exists
            if self.instance and self.instance.color:
                self.fields['color'].initial = str(self.instance.color.id)
            elif self.instance and self.instance.color_custom:
                self.fields['color'].initial = 'other'

    def clean(self):
        cleaned_data = super().clean()
        color_val = cleaned_data.get('color')
        color_custom = cleaned_data.get('color_custom', '').strip()

        # Resolve the Color object
        color_obj = None
        if color_val and color_val != 'other':
            try:
                color_obj = Color.objects.get(id=int(color_val))
            except (ValueError, Color.DoesNotExist):
                color_obj = None
        
        if not color_obj and not color_custom:
            self.add_error('color_custom', 'Please select a color or describe it in the custom field.')

        cleaned_data['color'] = color_obj
        return cleaned_data

class AddItemForm(forms.Form):
    """
    Form for adding an item with service selection for HTMX requests.
    """
    name = forms.CharField(max_length=100, required=True)
    color = forms.ChoiceField(
        choices=[],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select color-select'})
    )
    color_custom = forms.CharField(
        max_length=100, required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Describe the color (e.g. Olive Green)',
        })
    )
    quantity = forms.IntegerField(
        min_value=1, max_value=10, initial=1,
        widget=forms.Select(
            choices=[(i, str(i)) for i in range(1, 11)],
            attrs={'class': 'form-select form-select-sm'}
        )
    )
    category = forms.ModelChoiceField(queryset=ServiceCategory.objects.all(), required=True)
    package = forms.ModelChoiceField(queryset=Package.objects.none(), required=True)

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            color_choices = [('', 'Select color...')]
            color_choices += [(str(c.id), c.name) for c in Color.objects.filter(tenant=tenant)]
            color_choices.append(('other', 'Other / Custom...'))
            self.fields['color'].choices = color_choices
            
        if 'category' in self.data:
            try:
                category_id = int(self.data.get('category'))
                self.fields['package'].queryset = Package.objects.filter(category_id=category_id).order_by('service_type')
            except (ValueError, TypeError):
                pass

    def clean(self):
        cleaned_data = super().clean()
        color_val = cleaned_data.get('color')
        color_custom = cleaned_data.get('color_custom', '').strip()

        # Resolve the Color object if a valid ID was provided (not 'other' and not empty)
        color_obj = None
        if color_val and color_val != 'other':
            try:
                color_obj = Color.objects.get(id=int(color_val))
            except (ValueError, Color.DoesNotExist):
                color_obj = None
        
        # Validation: Either a standard color must be selected, or a custom one must be described
        if not color_obj and not color_custom:
            self.add_error('color_custom', 'Please select a color or describe it in the custom field.')

        # Set the resolved object back into cleaned_data for the view to use
        cleaned_data['color'] = color_obj
        return cleaned_data
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




class OrderForm_Antigraviy(forms.ModelForm):
    
    class Meta:
        model = Order
        fields = [
            'customer_name', 'customer_email', 'customer_phone', 'state', 'town', 'address', 'pickup_latitude', 'pickup_longitude',
            'delivery_option', 'recipient_name', 'recipient_email', 
            'recipient_phone', 'recipient_state', 'recipient_town', 'recipient_address', 'recipient_latitude', 'recipient_longitude',
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
            'state': forms.Select(attrs={
                'class': 'form-select select2', 
                'hx-get': reverse_lazy('laundry:htmx_get_towns'), 
                'hx-target': '#id_town', 
                'hx-trigger': 'change'
            }),
            'town': forms.Select(attrs={
                'class': 'form-select select2', 
                'id': 'id_town',
                'hx-get': reverse_lazy('laundry:htmx_calculate_deliverys'),
                'hx-target': '#delivery-price-display',
                'hx-trigger': 'change'
            }),
            'address': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_address', 'placeholder': 'Enter your pickup address'}),
            
            'delivery_option': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            
            'recipient_name': forms.TextInput(attrs={'class': 'form-control'}),
            'recipient_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'recipient_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'recipient_state': forms.Select(attrs={
                'class': 'form-select select2',
                'hx-get': reverse_lazy('laundry:htmx_get_towns'),
                'hx-target': '#id_recipient_town',
                'hx-trigger': 'change'
            }),
            'recipient_town': forms.Select(attrs={'class': 'form-select select2', 'id': 'id_recipient_town'}),
            'recipient_address': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_recipient_address', 'placeholder': 'Enter recipient address'}),
            'pickup_latitude': forms.HiddenInput(),
            'pickup_longitude': forms.HiddenInput(),
            'recipient_latitude': forms.HiddenInput(),
            'recipient_longitude': forms.HiddenInput(),
            
            'pickup_date': forms.DateTimeInput(
                attrs={'class': 'form-control', 'id': 'pickup-calendar', 'type': 'datetime-local'}
            ),
            'special_instructions': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 2,
                    'cols': 40,
                    'placeholder': 'Special care instructions...'
                }
            ),
        }
        labels = {
            'customer_name': 'Customer Name',
            'customer_email': 'Customer Email',
            'customer_phone': 'Customer Phone',
            'state': 'State',
            'town': 'Town',
            'address': 'Address',
            'recipient_state': 'Recipient State',
            'recipient_town': 'Recipient Town',
            'pickup_date': 'Pickup Date',
            'special_instructions': 'Special Instructions',
        }
        
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Auto-populate if user is in Customer group
        if user and user.is_authenticated:
            if user.groups.filter(name='Customer').exists():
                self.fields['customer_name'].initial = user.name
                self.fields['customer_email'].initial = user.email
                self.fields['customer_phone'].initial = user.phone
                self.fields['address'].initial = user.address
                self.fields['pickup_latitude'].initial = user.latitude
                self.fields['pickup_longitude'].initial = user.longitude

        # Make recipient and pickup coordinates optional by default
        optional_fields = [
            'recipient_name', 'recipient_email', 'recipient_phone', 
            'recipient_state', 'recipient_town', 'recipient_address', 
            'recipient_latitude', 'recipient_longitude',
            'pickup_latitude', 'pickup_longitude', 'delivery_option', 'special_instructions'
        ]
        for field in optional_fields:
            if field in self.fields:
                self.fields[field].required = False
        
        if 'delivery_option' in self.fields:
            self.fields['delivery_option'].initial = 'home_delivery'

        # Make all other fields required
        for field_name in self.fields:
            if field_name not in optional_fields:
                self.fields[field_name].required = True



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
