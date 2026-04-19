from math import log

from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponseForbidden
from .models import Tenant
from chromadb import logger

class TenantMiddleware(MiddlewareMixin):
    def process_request(self, request):
        host = request.get_host().split(":")[0]  # get domain without port
        logger.info(f"Processing request for host: {host}")

        allowed_dmc_hosts = [
            # "127.0.0.1",
            # "127.0.0.0",
            "laundry.dignityconcept.tech",
            "dignityconcept.tech"
        ]

        if host in allowed_dmc_hosts or host.endswith(".dignityconcept.tech"):
            try:
                request.tenant = Tenant.objects.get(code='DMC')
                logger.info(f"DMC tenant found for host: {host}")
            except Tenant.DoesNotExist:
                # Fallback if DMC tenant is not yet created in the DB
                request.tenant = None
            return None

        try:
            tenant = Tenant.objects.get(subdomain=host)
            request.tenant = tenant
            logger.info(f"Tenant found: {tenant.name} for host: {host}")
        except Tenant.DoesNotExist:
            return HttpResponseForbidden("Unknown or Unpermitted Website")
