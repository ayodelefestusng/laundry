import threading

# Global thread-local storage for request data
_thread_locals = threading.local()


def get_current_request():
    """Return the request object for the current thread."""
    return getattr(_thread_locals, "request", None)


def get_current_user():
    """Return the user object for the current thread."""
    return getattr(_thread_locals, "user", None)


class ThreadLocalMiddleware:
    """
    Middleware that puts the request object in thread local storage.
    This allows logging filters to access request data (user, tenant).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.request = request
        _thread_locals.user = getattr(request, "user", None)
        # Store simple strings for logging to avoid db hits in filter
        if request.user and request.user.is_authenticated:
            _thread_locals.user_str = request.user.email
            # Handle Tenant
            tenant = getattr(request.user, "tenant", None)
            if tenant:
                _thread_locals.tenant_str = str(tenant.name)
            else:
                _thread_locals.tenant_str = "No-Tenant"
        else:
            _thread_locals.user_str = "Anonymous"
            _thread_locals.tenant_str = "Public"

        try:
            response = self.get_response(request)
        finally:
            # Cleanup to prevent data leaking to other requests in the same thread
            _thread_locals.request = None
            _thread_locals.user = None
            _thread_locals.user_str = None
            _thread_locals.tenant_str = None

        return response


class CSRFDynamicOriginMiddleware:
    """
    Middleware that dynamically updates CSRF_TRUSTED_ORIGINS
    from active tenant subdomains at runtime.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self._origins_loaded = False

    def __call__(self, request):
        if not self._origins_loaded:
            self._update_csrf_origins()
            self._origins_loaded = True

        return self.get_response(request)

    def _update_csrf_origins(self):
        """Fetch active tenant subdomains and update CSRF_TRUSTED_ORIGINS."""
        try:
            from django.conf import settings
            from myapp.models import Tenant

            # Base origins (production + local)
            origins = [
                "https://whatsapp-1-vectra-laundry-app.xqqhik.easypanel.host",
            ]

            # Add local development origins
            for subdomain in ["localhost", "127.0.0.1"]:
                origins.append(f"http://{subdomain}:8000")

            # Fetch active tenants
            active_tenants = Tenant.objects.filter(is_active=True)
            
            for tenant in active_tenants:
                if tenant.subdomain:
                    # Production pattern
                    origins.append(f"https://{tenant.subdomain}.xqqhik.easypanel.host")
                    # Local development patterns
                    origins.append(f"http://{tenant.subdomain}.localhost:8000")
                    origins.append(f"http://{tenant.subdomain}.127.0.0.1:8000")

            # Remove duplicates
            unique_origins = list(dict.fromkeys(origins))

            # Update settings dynamically
            settings.CSRF_TRUSTED_ORIGINS = unique_origins
            
            import logging
            logging.getLogger(__name__).info(
                f"CSRF_TRUSTED_ORIGINS updated with {len(unique_origins)} origins: {unique_origins}"
            )

        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(
                f"Could not dynamically update CSRF_TRUSTED_ORIGINS: {e}"
            )
