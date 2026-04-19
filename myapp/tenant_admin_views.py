from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.apps import apps
from django import forms
from django.core.exceptions import ImproperlyConfigured

# Map URL parameters to models
MODEL_MAP = {
    'premiumclient': 'myapp.PremiumClient',
    'servicecategory': 'myapp.ServiceCategory',
    'package': 'myapp.Package',
    'servicechoices': 'myapp.ServiceChoices',
    'workflow': 'myapp.Workflow',
    'cluster': 'myapp.Cluster',
    'deliverypricing': 'myapp.DeliveryPricing',
    'tenant': 'myapp.Tenant',
    'tenantattribute': 'myapp.TenantAttribute',
    'user': 'myapp.CustomUser',
}

class TenantAdminMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Ensures user is an active tenant-assigned manager/staff.
    Dynamically loads the Model based on the URL parameter.
    Filters QuerySets securely to only elements owned by request.tenant.
    """
    def test_func(self):
        model_name = self.kwargs.get('model_name')
        if model_name == 'tenant':
            return self.request.user.is_superuser
        if model_name in ['tenantattribute', 'user']:
            return self.request.user.is_superuser or (
                self.request.user.is_staff and
                hasattr(self.request, 'tenant') and
                self.request.user.groups.filter(name='Partner').exists()
            )
        # Allow entry if they are staff and have a tenant OR superuser
        return self.request.user.is_superuser or (self.request.user.is_staff and hasattr(self.request, 'tenant'))

    def get_model(self):
        model_name = self.kwargs.get('model_name')
        if model_name not in MODEL_MAP:
            raise ImproperlyConfigured(f"Model {model_name} is not registered for Tenant Admin.")
        return apps.get_model(MODEL_MAP[model_name])
    
    def get_queryset(self):
        model = self.get_model()
        qs = model.objects.all()
        # Enforce Tenant filtering if the model has a tenant field relation
        if hasattr(model, 'tenant'):
            qs = qs.filter(tenant=self.request.tenant)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model_name'] = self.kwargs.get('model_name')
        context['model_name_plural'] = self.get_model()._meta.verbose_name_plural
        
        # Decide what fields to show in the list view
        model = self.get_model()
        if hasattr(model, 'get_admin_list_display'):
            context['list_display'] = model.get_admin_list_display()
        else:
            # Fallback to intelligent guessing
            fields = [f.name for f in model._meta.fields if f.name not in ['id', 'tenant', 'password']]
            context['list_display'] = fields[:4] # max 4 columns
            
        return context

class TenantGenericListView(TenantAdminMixin, ListView):
    template_name = 'tenant_admin_list.html'

class TenantGenericFormMixin:
    """Auto-generates a ModelForm without tenant and injects it on save"""
    def get_form_class(self):
        model_cls = self.get_model()
        model_name = self.kwargs.get('model_name')
        class GenericModelForm(forms.ModelForm):
            class Meta:
                model = model_cls
                # Standard exclusion for multi-tenant isolation
                exclude = ['tenant', 'password', 'mfa_secret', 'groups', 'user_permissions']
                
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                if model_name == 'user' and self.instance.pk:
                    # On edit:
                    # Allow editing of email, is_active, phone number and name.
                    allowed_fields = ['email', 'is_active', 'phone', 'name']
                    self.fields = {k: v for k, v in self.fields.items() if k in allowed_fields}
        return GenericModelForm
        
    def form_valid(self, form):
        # Auto inject tenant if field exists and it's not a global Tenant model mapping
        model_name = self.kwargs.get('model_name')
        if hasattr(form.instance, 'tenant_id') and model_name != 'tenant':
            if not form.instance.tenant_id:
                form.instance.tenant = self.request.tenant
                
        response = super().form_valid(form)
        
        # Cross-cutting concerns based on model and action
        from django.core.mail import EmailMultiAlternatives
        from django.template.loader import render_to_string
        from django.utils.html import strip_tags
        from django.contrib.auth.tokens import default_token_generator
        from django.urls import reverse
        from myapp.models import CustomUser
        from django.contrib.auth.models import Group
        
        is_create = not self.object or not getattr(self, '_was_update', False)
        
        if model_name == 'tenant' and is_create:
            # Create a user with tenant email, set is_staff=True
            tenant = self.object
            # We assume tenant has a primary contact email field, 
            # but if it doesn't, we might need it from another source. Currently using custom input via forms might be needed.
            # However, Tenant model has no email. We might just create a default admin user based on subdomain?
            # Creating one for the tenant based on request input email? 
            # I will use a dummy one unless it's in the payload.
            email = self.request.POST.get('email', f"admin@{tenant.subdomain}.com")
            user, created = CustomUser.objects.get_or_create(
                email=email,
                defaults={'name': f"{tenant.name} Admin", 'is_staff': True, 'tenant': tenant}
            )
            if created:
                partner_group, _ = Group.objects.get_or_create(name='Partner')
                user.groups.add(partner_group)
                
            if not user.has_usable_password():
                token = default_token_generator.make_token(user)
                link = self.request.build_absolute_uri(reverse("laundry:setup_password", args=[user.pk, token]))
                
                subject = "Setup your Tenant Dashboard account"
                html_message = render_to_string("emails/register_email.html", {"user": user, "create_link": link, "ceate_link": link})
                msg = EmailMultiAlternatives(subject, strip_tags(html_message), None, [user.email])
                msg.attach_alternative(html_message, "text/html")
                msg.send()
                
        elif model_name == 'tenantattribute':
            # Create or Edit
            tenant_attr = self.object
            admin_users = CustomUser.objects.filter(tenant=tenant_attr.tenant, is_staff=True)
            emails = [u.email for u in admin_users]
            if emails:
                subject = "Tenant Attributes Updated"
                message = f"Tenant {tenant_attr.brand_name} attributes updated.\nWhatsApp: {tenant_attr.whatsapp_number}\nAddress: {tenant_attr.address}"
                msg = EmailMultiAlternatives(subject, message, None, emails)
                msg.send()
                
        elif model_name == 'user' and is_create:
            user = self.object
            if user.is_staff and not user.has_usable_password():
                token = default_token_generator.make_token(user)
                link = self.request.build_absolute_uri(reverse("laundry:setup_password", args=[user.pk, token]))
                
                subject = "Setup your account"
                html_message = render_to_string("emails/register_email.html", {"user": user, "create_link": link, "ceate_link": link})
                msg = EmailMultiAlternatives(subject, strip_tags(html_message), None, [user.email])
                msg.attach_alternative(html_message, "text/html")
                msg.send()

        return response
        
    def get_success_url(self):
        return reverse_lazy('laundry:tenant_admin_list', kwargs={'model_name': self.kwargs.get('model_name')})

class TenantGenericCreateView(TenantAdminMixin, TenantGenericFormMixin, CreateView):
    template_name = 'tenant_admin_form.html'
    
    def form_valid(self, form):
        self._was_update = False
        return super().form_valid(form)

class TenantGenericUpdateView(TenantAdminMixin, TenantGenericFormMixin, UpdateView):
    template_name = 'tenant_admin_form.html'
    
    def form_valid(self, form):
        self._was_update = True
        return super().form_valid(form)

class TenantGenericDeleteView(TenantAdminMixin, DeleteView):
    template_name = 'tenant_admin_confirm_delete.html'
    def get_success_url(self):
        return reverse_lazy('laundry:tenant_admin_list', kwargs={'model_name': self.kwargs.get('model_name')})

def tenant_admin_hub(request):
    """Renders the settings hub portal"""
    if not request.user.is_staff:
        return redirect('laundry:homepage')
    return render(request, 'tenant_admin_hub.html')
