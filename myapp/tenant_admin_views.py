from math import log

from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.apps import apps
from django import forms
from django.core.exceptions import ImproperlyConfigured
from chromadb import logger

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
    'color': 'myapp.Color',
    # Landing Page Content Models
    'landingcarousel': 'myapp.LandingCarousel',
    'landingtext': 'myapp.LandingText',
    'landingvalue': 'myapp.LandingValue',
    'landingcommitment': 'myapp.LandingCommitment',
    'landingpricingcard': 'myapp.LandingPricingCard',
    'landingcustomerstory': 'myapp.LandingCustomerStory',
    'landingfaq': 'myapp.LandingFAQ',
}

class TenantAdminMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Ensures user is an active tenant-assigned manager/staff.
    Dynamically loads the Model based on the URL parameter.
    Filters QuerySets securely to only elements owned by request.tenant.
    """
    def _is_aggregator(self):
        return self.request.user.groups.filter(name='Aggregator').exists()

    def test_func(self):
        logger.info(f"TenantAdminMixin test_func: {self.request.user}")
        model_name = self.kwargs.get('model_name')
        if model_name == 'tenant':
            # Superuser: full access | Aggregator: can list/create their own tenants
            return self.request.user.is_superuser or self._is_aggregator()
        if model_name in ['tenantattribute', 'user']:
            logger.info(f"TenantAdmin test_func2: {self.request.user.is_staff}")
            logger.info(f"TenantAdmin test_func3: {self.request.user.groups.filter(name='Partner').exists()}")
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
            logger.warning(f"TenantAdminMixin get_model: {model_name} is not registered for Tenant Admin.")
            raise ImproperlyConfigured(f"Model {model_name} is not registered for Tenant Admin.")
        logger.info(f"TenantAdminMixin get_model 2: {MODEL_MAP[model_name]}")
        return apps.get_model(MODEL_MAP[model_name])
    
    def get_queryset(self):
        model = self.get_model()
        model_name = self.kwargs.get('model_name')
        qs = model.objects.all()

        if model_name == 'tenant':
            # Aggregators see only tenants they created; superusers see all
            if not self.request.user.is_superuser:
                qs = qs.filter(created_by=self.request.user)
            return qs

        # Enforce Tenant filtering if the model has a tenant field relation
        if hasattr(model, 'tenant'):
            qs = qs.filter(tenant=self.request.tenant)
            logger.info(f"TenantAdminMixin get_queryset: {qs}")
        logger.info(f"TenantAdminMixin get_queryset 2: {qs}")
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model_name'] = self.kwargs.get('model_name')
        context['model_name_plural'] = self.get_model()._meta.verbose_name_plural
        
        # Decide what fields to show in the list view
        model = self.get_model()
        if hasattr(model, 'get_admin_list_display'):
            logger.info(f"TenantAdminMixin get_context_data: {model.get_admin_list_display()}")
            context['list_display'] = model.get_admin_list_display()
        else:
            # Fallback to intelligent guessing
            logger.info(f"TenantAdminMixin get_context_data 2: {model._meta.fields}")
            fields = [f.name for f in model._meta.fields if f.name not in ['id', 'tenant', 'password']]
            context['list_display'] = fields[:4] # max 4 columns
        logger.info(f"TenantAdminMixin get_context_data 3: {context['list_display']}")
        return context


class TenantGenericListView(TenantAdminMixin, ListView):
    logger.info(f"TenantAdminMixin:")
    template_name = 'tenant_admin_list.html'

class TenantGenericFormMixin:
    """Auto-generates a ModelForm without tenant and injects it on save"""
    def get_form_class(self):
        logger.info(f"TenantAdminMixin get_form_class: {self.request.user}")
        model_cls = self.get_model()
        model_name = self.kwargs.get('model_name')
        class GenericModelForm(forms.ModelForm):
            class Meta:
                model = model_cls
                # Standard exclusion for multi-tenant isolation
                exclude = ['tenant', 'mfa_secret', 'groups', 'user_permissions']
                # Include password for Tenant model (SMTP credentials)
                if model_name == 'tenant':
                    exclude = ['tenant', 'mfa_secret', 'groups', 'user_permissions', 'password']
                    
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                if 'created_by' in self.fields:
                    del self.fields['created_by']
                
                # For Tenant model, include password field for SMTP credentials
                if model_name == 'tenant':
                    self.fields['password'] = forms.CharField(
                        label="SMTP Password",
                        required=False,
                        widget=forms.PasswordInput(attrs={'placeholder': 'Email SMTP password for sending emails'}),
                        help_text="SMTP password for tenant email configuration"
                    )
                    self.fields['password'].help_text = "Enter the SMTP password for the tenant's email (vectra_email)"
                    
                if model_name == 'user' and self.instance.pk:
                    logger.info(f"TenantAdminMixin get_form_class 2: {self.request.user}")
                    # On edit:
                    # Allow editing of email, is_active, phone number and name.
                    allowed_fields = ['email', 'is_active', 'phone', 'name']
                    self.fields = {k: v for k, v in self.fields.items() if k in allowed_fields}
                    
                if model_name == 'tenantattribute':
                    allowed_fields = ['brand_name', 'logo', 'primary_color', 'secondary_color', 'font_family', 'whatsapp_number', 'address']
                    self.fields = {k: v for k, v in self.fields.items() if k in allowed_fields}
        logger.info(f"TenantAdminMixin get_form_class 3: {GenericModelForm}")
        return GenericModelForm
        
    def form_valid(self, form):
        # Auto inject tenant if field exists and it's not a global Tenant model mapping
        model_name = self.kwargs.get('model_name')
        if hasattr(form.instance, 'tenant_id') and model_name != 'tenant':
            if not form.instance.tenant_id:
                logger.info(f"TenantAdminMixin form_valid: {self.request.user}")
                form.instance.tenant = self.request.tenant
        logger.info(f"Tenant Valid Form Submitted: {form.instance}")        
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
            logger.info(f"TenantAdminMixin form_valid 2: {self.request.user}")
            # Stamp created_by with the current user
            form.instance.created_by = self.request.user
            
            # Save SMTP password from form to tenant
            password = form.cleaned_data.get('password')
            if password:
                form.instance.password = password
                form.instance.save()  # Explicitly save to persist the password
                logger.info(f"Tenant SMTP password set form_valid: {self.request.user}")
            # Create a user with tenant email, set is_staff=True
            tenant = self.object
            email = tenant.email if tenant.email else f"admin@{tenant.subdomain}.com"
            user, created = CustomUser.objects.get_or_create(
                email=email,
                defaults={'name': f"{tenant.name} Admin", 'phone': tenant.phone, 'is_staff': True, 'tenant': tenant}
            )
            if created:
                logger.info(f"Tenant created form_valid: {self.request.user}")
                partner_group, _ = Group.objects.get_or_create(name='Partner')
                user.groups.add(partner_group)
                
            if not user.password or not user.has_usable_password():
                logger.info(f"Tenant password not set form_valid: {self.request.user}")
                token = default_token_generator.make_token(user)
                link = self.request.build_absolute_uri(reverse("laundry:setup_password", args=[user.pk, token]))
                
                subject = "Setup your Tenant Dashboard account"
                html_message = render_to_string("emails/register_email.html", {"user": user, "create_link": link, "ceate_link": link})
                logger.info(f"Tenant admin email prepared form_valid for  {user.email}---: {self.request.user}")
                from myapp.tasks import send_email_async
                send_email_async.delay(
                    subject=subject,
                    text_content=strip_tags(html_message),
                    html_content=html_message,
                    to_emails=[user.email],
                    tenant_id=tenant.id if tenant else None
                )
                logger.info(f"Tenant admin email sent form_valid for  {user.email}---: {self.request.user}")
            
            # --- Auto-seed default landing page content for the new tenant ---
            try:
                self._seed_landing_defaults(tenant)
                logger.info(f"Landing page defaults seeded for tenant: {tenant.name}")
            except Exception as e:
                logger.error(f"Failed to seed landing defaults for tenant {tenant.name}: {e}", exc_info=True)
        elif model_name == 'tenant' and not is_create:
            # Update case - save SMTP password if provided
            password = form.cleaned_data.get('password')
            if password:
                form.instance.password = password
                form.instance.save()  # Explicitly save to persist the password
                logger.info(f"Tenant SMTP password updated form_valid: {self.request.user}")
        elif model_name == 'tenantattribute':
            # Create or Edit
            tenant_attr = self.object
            admin_users = CustomUser.objects.filter(tenant=tenant_attr.tenant, is_staff=True)
            emails = [u.email for u in admin_users]
            if emails:
                logger.info(f"Tenant attributes updated form_valid: {self.request.user}")
                subject = "Tenant Attributes Updated"
                message = f"Tenant {tenant_attr.brand_name} attributes updated.\nWhatsApp: {tenant_attr.whatsapp_number}\nAddress: {tenant_attr.address}"
                from myapp.tasks import send_email_async
                send_email_async.delay(
                    subject=subject,
                    text_content=message,
                    html_content=None,
                    to_emails=emails,
                    tenant_id=tenant_attr.tenant.id if tenant_attr.tenant else None
                )
                
        elif model_name == 'user' and is_create:
            logger.info(f"User created form_valid: {self.request.user}")
            user = self.object
            if user.is_staff and (not user.password or not user.has_usable_password()):
                logger.info(f"User password not set form_valid: {self.request.user}")
                token = default_token_generator.make_token(user)
                link = self.request.build_absolute_uri(reverse("laundry:setup_password", args=[user.pk, token]))
                
                subject = "Setup your account"
                html_message = render_to_string("emails/register_email.html", {"user": user, "create_link": link, "ceate_link": link})
                from myapp.tasks import send_email_async
                send_email_async.delay(
                    subject=subject,
                    text_content=strip_tags(html_message),
                    html_content=html_message,
                    to_emails=[user.email],
                    tenant_id=user.tenant.id if user.tenant else None
                )
                logger.info(f"User password not set form_valid: {self.request.user}")
                logger.info(f"Email sent to: {user.email}")
        logger.info(f"TenantAdminMixin form valid: {response}")
        return response
        
    def get_success_url(self):
        logger.info(f"TenantAdminMixin get_success_url: {self.request.user}")
        return reverse_lazy('laundry:tenant_admin_list', kwargs={'model_name': self.kwargs.get('model_name')})

    def _seed_landing_defaults(self, tenant):
        """Auto-populate landing page models with default content for a new tenant."""
        from myapp.landing_models import (
            LandingText, LandingValue, LandingCommitment,
            LandingPricingCard, LandingCustomerStory, LandingFAQ,
        )

        # 1. Hero Text
        LandingText.objects.create(
            tenant=tenant,
            hero_title="Laundry Made Simple, Fresh & Fast.",
            hero_subtitle="Experience premium garment care with free doorstep pickup & delivery. Eco-friendly cleaning that preserves your clothes and the planet.",
        )

        # 2. Value Propositions
        LandingValue.objects.bulk_create([
            LandingValue(tenant=tenant, value_text="Free Pickup & Delivery", value_subtext="Right from your doorstep", icon_class="fas fa-truck-fast"),
            LandingValue(tenant=tenant, value_text="24h Turnaround", value_subtext="Express services available", icon_class="fas fa-stopwatch"),
            LandingValue(tenant=tenant, value_text="Eco-Friendly Care", value_subtext="Non-toxic, safe detergents", icon_class="fas fa-leaf"),
        ])

        # 3. About / Commitment
        LandingCommitment.objects.create(
            tenant=tenant,
            committed_to="Committed to Garment Care and Our Community",
            we_believe="We believe that doing laundry shouldn't cost the earth. That's why we've pioneered a sustainable approach to garment care.",
            eco_friendly="Non-toxic Detergents: Safe for sensitive skin and the environment.",
        )

        # 4. Pricing Cards
        LandingPricingCard.objects.bulk_create([
            LandingPricingCard(
                tenant=tenant, title="Wash & Fold", is_popular=False,
                description="Perfect for everyday wear.", price=800,
                features=["Wash & Tumble Dry", "Neat Folding", "Eco-friendly Detergents"],
            ),
            LandingPricingCard(
                tenant=tenant, title="Wash & Iron", is_popular=True,
                description="Crisp, wrinkle-free garments.", price=1200,
                features=["Wash & Steam Iron", "Premium Hanger Pack", "Spot Treatment"],
            ),
            LandingPricingCard(
                tenant=tenant, title="Premium Dry Clean", is_popular=False,
                description="For delicate & special fabrics.", price=2500,
                features=["Chemical-free Solvents", "Hand Finishing", "Minor Alterations"],
            ),
        ])

        # 5. Customer Stories
        LandingCustomerStory.objects.bulk_create([
            LandingCustomerStory(
                tenant=tenant,
                story="I absolutely loved how fresh and neatly folded my clothes arrived. There was no harsh smell, no wrinkles, and the fabric felt softer than before. Genuinely stress-free.",
                name="Happy Customer", stars=5, is_verified=True,
            ),
            LandingCustomerStory(
                tenant=tenant,
                story="I trusted them with my delicate gowns and formal outfits, and they returned looking brand-new. The shine, shape, and texture were perfectly maintained. Truly world-class.",
                name="Satisfied Client", stars=5, is_verified=True,
            ),
            LandingCustomerStory(
                tenant=tenant,
                story="The curtains and sofa covers I sent were returned spotless, neatly packed, and smelling wonderfully fresh. Dust vanished without harming fabric colour. Highly recommend!",
                name="Loyal Customer", stars=5, is_verified=True,
            ),
        ])

        # 6. FAQs
        LandingFAQ.objects.bulk_create([
            LandingFAQ(
                tenant=tenant,
                question="What is your turnaround time?",
                answer="Standard delivery takes 48-72 hours. We also offer Express Delivery for a 24-hour turnaround at a minimal extra charge.",
            ),
            LandingFAQ(
                tenant=tenant,
                question="What if I'm not home for pickup or delivery?",
                answer='You can leave your laundry bag with your concierge, security desk, or a designated safe spot. Just let us know in the "Special Instructions" when booking.',
            ),
            LandingFAQ(
                tenant=tenant,
                question="Do you mix my clothes with others?",
                answer="Absolutely not. We process every customer's order individually in dedicated machines to maintain strict hygiene standards and ensure garments are never mixed.",
            ),
        ])

class TenantGenericCreateView(TenantAdminMixin, TenantGenericFormMixin, CreateView):
    template_name = 'tenant_admin_form.html'
    
    def form_valid(self, form):
        logger.info(f"TenantAdminMixin form_create: {self.request.user}")
        self._was_update = False
        return super().form_valid(form)

class TenantGenericUpdateView(TenantAdminMixin, TenantGenericFormMixin, UpdateView):
    template_name = 'tenant_admin_form.html'

    def test_func(self):
        """Aggregators can only edit tenants they created."""
        if not super().test_func():
            return False
        model_name = self.kwargs.get('model_name')
        if model_name == 'tenant' and not self.request.user.is_superuser:
            obj = self.get_object()
            return obj.created_by == self.request.user
        return True

    def form_valid(self, form):
        logger.info(f"TenantAdminMixin form_update: {self.request.user}")
        self._was_update = True
        return super().form_valid(form)

class TenantGenericDeleteView(TenantAdminMixin, DeleteView):
    template_name = 'tenant_admin_confirm_delete.html'

    def test_func(self):
        """Aggregators can only delete tenants they created."""
        if not super().test_func():
            return False
        model_name = self.kwargs.get('model_name')
        if model_name == 'tenant' and not self.request.user.is_superuser:
            obj = self.get_object()
            return obj.created_by == self.request.user
        return True

    def get_success_url(self):
        logger.info(f"TenantAdminMixin get_success_url: {self.request.user}")
        return reverse_lazy('laundry:tenant_admin_list', kwargs={'model_name': self.kwargs.get('model_name')})

def tenant_admin_hub(request):
    """Renders the settings hub portal"""
    if not request.user.is_staff:
        logger.info(f"TenantAdminMixin tenant_admin_hub: {request.user}")
        return redirect('laundry:homepage')
    logger.info(f"TenantAdminMixin tenant_admin_hub 2: {request.user}")
    
    # Get tenants for QR generation (superuser/aggregator only)
    tenants = []
    is_superuser_or_aggregator = request.user.is_superuser or request.user.groups.filter(name='Aggregator').exists()
    if is_superuser_or_aggregator:
        from myapp.models import Tenant
        if request.user.is_superuser:
            tenants = Tenant.objects.filter(is_active=True)
        else:
            # Aggregator sees only their created tenants
            tenants = Tenant.objects.filter(created_by=request.user, is_active=True)
    
    context = {
        'tenants': tenants,
        'is_superuser_or_aggregator': is_superuser_or_aggregator,
    }
    return render(request, 'tenant_admin_hub.html', context)


def generate_qr_codes(request):
    
    """Generate QR codes and return PDF for download"""
    from django.http import HttpResponse
    from django.shortcuts import redirect
    from myapp.models import Tenant, QR
    from myapp.utils import get_signed_token
    import uuid
    import qrcode
    from io import BytesIO
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import ImageReader
    logger.info(f"Generating QR codes for tenant: {request.user}")
    # Determine tenant
    tenant_id = request.GET.get('tenant_id')
    quantity = int(request.GET.get('quantity', 100))
    
    is_superuser_or_aggregator = request.user.is_superuser or request.user.groups.filter(name='Aggregator').exists()
    
    if tenant_id:
        logger.info(f"Generating QR codes for tenant: {request.user}")
        try:
            tenant = Tenant.objects.get(id=tenant_id, is_active=True)
        except Tenant.DoesNotExist:
            logger.warning(f"QR Generation: Tenant {tenant_id} not found or inactive")
            return redirect('laundry:tenant_admin_hub')
    else:
        # Non-superuser/aggregator uses their own tenant
        if hasattr(request, 'tenant'):
            tenant = request.tenant
        else:
            logger.warning(f"QR Generation: No tenant found for user {request.user}")
            return redirect('laundry:tenant_admin_hub')
    
    # Verify permission for superuser/aggregator
    if is_superuser_or_aggregator and tenant_id:
        if not request.user.is_superuser:
            if tenant.created_by != request.user:
                logger.warning(f"QR Generation: User {request.user} tried to generate QR for tenant {tenant_id} they don't own")
                return redirect('laundry:tenant_admin_hub')
    
    # Generate QR codes
    from django.utils import timezone
    qr_list = []
    for _ in range(quantity):
        raw_uuid = str(uuid.uuid4())
        signed_code = get_signed_token(raw_uuid)
        qr_list.append(QR(
            code=signed_code, 
            tenant=tenant, 
            status='unused',
            created_by=request.user,
            date_created=timezone.now()
        ))
    
    QR.objects.bulk_create(qr_list)
    logger.info(f"QR Generation: Created {len(qr_list)} QR codes for tenant {tenant.name}")
    
    # Generate PDF
    qr_queryset = QR.objects.filter(tenant=tenant).order_by('-id')[:quantity]
    
    # Create PDF response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="qr_codes_{tenant.name}_{quantity}.pdf"'
    
    # Generate PDF
    c = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    
    cols = 5
    rows = 10
    margin = 35
    cell_width = (width - 2 * margin) / cols
    cell_height = (height - 2 * margin) / rows
    
    for i, qr in enumerate(qr_queryset):
        if i > 0 and i % (cols * rows) == 0:
            c.showPage()
            
        page_idx = i % (cols * rows)
        col = page_idx % cols
        row = page_idx // cols
        
        x = margin + col * cell_width
        y = height - margin - (row + 1) * cell_height
        
        # Generate QR image
        qr_img = qrcode.QRCode(box_size=10, border=4)
        qr_img.add_data(qr.code)
        qr_img.make(fit=True)
        img_buffer = qr_img.make_image(fill_color="black", back_color="white")
        img_bytes = BytesIO()
        img_buffer.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        img = ImageReader(BytesIO(img_bytes.getvalue()))
        
        qr_size = 80
        pad_x = (cell_width - qr_size) / 2
        pad_y = (cell_height - qr_size) / 2 + 10
        
        c.drawImage(img, x + pad_x, y + pad_y, width=qr_size, height=qr_size)
        
        c.setFont("Helvetica", 6)
        display_code = (qr.code[:30] + '..') if len(qr.code) > 30 else qr.code
        c.drawCentredString(x + cell_width/2, y + pad_y - 12, display_code)
    
    c.save()
    return response
