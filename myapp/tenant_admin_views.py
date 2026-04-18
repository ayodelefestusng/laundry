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
    'employee': 'myapp.Employee',
}

class TenantAdminMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Ensures user is an active tenant-assigned manager/staff.
    Dynamically loads the Model based on the URL parameter.
    Filters QuerySets securely to only elements owned by request.tenant.
    """
    def test_func(self):
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
        class GenericModelForm(forms.ModelForm):
            class Meta:
                model = model_cls
                exclude = ['tenant'] # Standard exclusion for multi-tenant isolation
        return GenericModelForm
        
    def form_valid(self, form):
        # Auto inject tenant if field exists
        if hasattr(form.instance, 'tenant_id'):
            form.instance.tenant = self.request.tenant
        return super().form_valid(form)
        
    def get_success_url(self):
        return reverse_lazy('laundry:tenant_admin_list', kwargs={'model_name': self.kwargs.get('model_name')})

class TenantGenericCreateView(TenantAdminMixin, TenantGenericFormMixin, CreateView):
    template_name = 'tenant_admin_form.html'

class TenantGenericUpdateView(TenantAdminMixin, TenantGenericFormMixin, UpdateView):
    template_name = 'tenant_admin_form.html'

class TenantGenericDeleteView(TenantAdminMixin, DeleteView):
    template_name = 'tenant_admin_confirm_delete.html'
    def get_success_url(self):
        return reverse_lazy('laundry:tenant_admin_list', kwargs={'model_name': self.kwargs.get('model_name')})

def tenant_admin_hub(request):
    """Renders the settings hub portal"""
    if not request.user.is_staff:
        return redirect('laundry:homepage')
    return render(request, 'tenant_admin_hub.html')
