from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponseForbidden
from .models import Tenant

class TenantMiddleware(MiddlewareMixin):
    def process_request(self, request):
        host = request.get_host().split(":")[0]  # get domain without port

        # allowed_dmc_hosts = [
        #     "127.0.0.1",
        #     "127.0.0.0",
        #     "laundry.dignityconcept.tech",
        #     "dignityconcept.tech"
        # ]

        # if host in allowed_dmc_hosts or host.endswith(".dignityconcept.tech"):
        allowed_dmc_hosts = [
            "127.0.0.1",
            "127.0.0.0",
               "localhost",
            "whatsapp-1-vectra-laundry-app.xqqhik.easypanel.host",
            "ayo.vectra.ng",
            "laundry.dignityconcept.tech",
            "dignityconcept.tech",
            "http://localhost:8000/"
        ]

        if host in allowed_dmc_hosts or host.endswith(".dignityconcepts.tech"):
            try:
                request.tenant = Tenant.objects.get(code='DMC')
            except Tenant.DoesNotExist:
                # Fallback if DMC tenant is not yet created in the DB
                request.tenant = None
            return None

        try:
            tenant = Tenant.objects.get(subdomain=host)
            request.tenant = tenant
        except Tenant.DoesNotExist:
            return HttpResponseForbidden("Unknown or Unpermitted Website")
