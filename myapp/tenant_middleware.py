from django.utils.deprecation import MiddlewareMixin
from .models import Tenant

class TenantMiddleware(MiddlewareMixin):
    def process_request(self, request):
        host = request.get_host().split(":")[0]  # get domain without port
        try:
            tenant = Tenant.objects.get(subdomain=host)
            request.tenant = tenant
        except Tenant.DoesNotExist:
            request.tenant = None  # fallback or raise error
