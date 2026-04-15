from .models import Tenant

def tenant_assets(request):
    """
    Injects tenant-specific assets (logo, colors, fonts) into the template context.
    """
    tenant = getattr(request, 'tenant', None)
    if tenant:
        return {
            'tenant_primary_color': tenant.primary_color or '#007bff',
            'tenant_secondary_color': tenant.secondary_color or '#6c757d',
            'tenant_font_family': tenant.font_family or 'system-ui, -apple-system, sans-serif',
            'tenant_logo_url': tenant.logo.url if tenant.logo else None,
            'tenant_name': tenant.name,
        }
    return {}
