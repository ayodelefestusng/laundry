from .models import Tenant

def tenant_assets(request):
    """
    Injects tenant-specific assets (logo, colors, fonts) into the template context.
    """
    tenant = getattr(request, 'tenant', None)
    if tenant:
        # Avoid crashing if TenantAttribute is missing for an old Tenant
        attr = getattr(tenant, 'attribute', None)
        whatsapp_number = attr.whatsapp_number if attr else ''
        # Normalize Nigerian numbers: replace leading 0 with +234
        if whatsapp_number.startswith('0'):
            whatsapp_number = '+234' + whatsapp_number[1:]
            
        try:
            logo_url = request.build_absolute_uri(attr.logo.url) if attr and attr.logo else None
        except Exception:
            logo_url = None
            
        return {
            'tenant_primary_color': attr.primary_color if attr else '#007bff',
            'tenant_brand': attr.brand_name if attr else 'Laundry Business Solution',
            'tenant_secondary_color': attr.secondary_color if attr else '#6c757d',
            'tenant_font_family': attr.font_family if attr else 'system-ui, -apple-system, sans-serif',
            'tenant_logo_url': logo_url,
            'tenant_name': tenant.name,
            'tenant_whatsapp_number': whatsapp_number,
        }
    return {}
