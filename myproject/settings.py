"""
Django settings for myproject project.
"""

from pathlib import Path
import os
import django
from dotenv import load_dotenv
from yaml import compose

# Load environment variables from a .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================================================================
#  Core Settings
# ==============================================================================

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = os.getenv("DEBUG", "True") == "True"
DEBUG="true"

# ALLOWED_HOSTS = ['*'] # Change to specific domain names in production
ALLOWED_HOSTS = [
    '*',  # Allow all hosts (not recommended for production)
    "tenant1.com",
    "tenant2.com",
    "tenant3.com",
    "yourmainapp.com",
    "whatsapp-1-laundry-2-compose.xqqhik.easypanel.host",
]


# ==============================================================================
#  Application Definition
# ==============================================================================

INSTALLED_APPS = [
    # My apps
    'myapp', # Correct app name

    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'crispy_forms',
    'crispy_bootstrap5', # Needed for Bootstrap 5 template pack
    'whitenoise.runserver_nostatic', # For serving static files in development
    'django.contrib.humanize',
    'django_otp',
    'django_otp.plugins.otp_totp',
    'django_otp.plugins.otp_static',
    'django_otp.plugins.otp_email',
    'django_htmx',   # optional, for enhanced HTMX support
  
  
    # Allauth apps
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    # Add providers if needed, e.g.:
    'allauth.socialaccount.providers.google',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # For serving static files in production
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "myapp.tenant_middleware.TenantMiddleware",
    "myapp.middleware.CSRFDynamicOriginMiddleware",

    # Allauth middleware
    'allauth.account.middleware.AccountMiddleware',
    'django_htmx.middleware.HtmxMiddleware',  # ✅ valid middlewar

]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


ROOT_URLCONF = 'myproject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'myapp.context_processors.tenant_assets',
            ],
        },
    },
]

WSGI_APPLICATION = 'myproject.wsgi.application'

# ==============================================================================
#  Database & Auth
# ==============================================================================

import dj_database_url

_db_config = dj_database_url.config(
    default=os.getenv("DATABASE_URI", f"sqlite:///{os.path.join(BASE_DIR, 'db.sqlite3')}"),
    conn_max_age=600,
    conn_health_checks=True,
)
# Add timeout options for PostgreSQL to prevent hanging on bad network
if _db_config.get('ENGINE') == 'django.db.backends.postgresql':
    _db_config.setdefault('OPTIONS', {}).update({
        'connect_timeout': 10,
        'options': '-c statement_timeout=30000',  # 30 seconds max per statement
    })
DATABASES = {'default': _db_config}
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

# AUTH_USER_MODEL = 'myapp.CustomUser' # Correct user model reference
AUTH_USER_MODEL = 'myapp.CustomUser'


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_REDIRECT_URL = 'laundry:customer_order'
LOGOUT_REDIRECT_URL = 'laundry:login'
LOGIN_URL = 'laundry:login'


# ==============================================================================
#  Internationalization & Time
# ==============================================================================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Lagos'
USE_I18N = True
USE_TZ = True

# ==============================================================================
#  Static & Media Files
# ==============================================================================

STATIC_URL = 'static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


def get_csrf_trusted_origins():
    """
    Dynamically fetch CSRF_TRUSTED_ORIGINS from active tenants.
    Called at runtime to include all active tenant subdomains.
    """
    origins = [
        "https://whatsapp-1-vectra-laundry-app.xqqhik.easypanel.host",  # Fallback/production
    ]
    
    try:
        # Import here to avoid circular imports at settings load time
        from myapp.models import Tenant
        from django.conf import settings
        
        # Get all active tenants
        active_tenants = Tenant.objects.filter(is_active=True)
        
        for tenant in active_tenants:
            if tenant.subdomain:
                # Add common deployment patterns
                origins.append(f"https://{tenant.subdomain}.xqqhik.easypanel.host")
                origins.append(f"http://{tenant.subdomain}.localhost:8000")
                origins.append(f"http://{tenant.subdomain}.127.0.0.1:8000")
                origins.append(f"http://{tenant.subdomain}.127.0.0.1:8002")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_origins = []
        for origin in origins:
            if origin not in seen:
                seen.add(origin)
                unique_origins.append(origin)
        
        return unique_origins
    except Exception as e:
        # If database isn't ready yet, return fallback origins
        import logging
        logging.getLogger(__name__).warning(f"Could not load tenant origins: {e}")
        return origins

raw_origins = os.getenv("CSRF_TRUSTED_ORIGINS", "")
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
# Default CSRF_TRUSTED_ORIGINS (fallback until database is ready)
CSRF_TRUSTED_ORIGINS.extend([
     "https://whatsapp-1-vectra-laundry-app.xqqhik.easypanel.host",
    "http://dignityconcept.tech",
    "https://dignityconcept.tech",
    "http://www.dignityconcept.tech",
    "https://www.dignityconcept.tech",
    "http://vectra.ng",
    "https://vectra.ng",
    "http://www.vectra.ng",
    "https://www.vectra.ng",
    "https://whatsapp-1-laundry-2-compose.xqqhik.easypanel.host",
    "https://whatsapp-1-laundry-2-compose.xqqhik.easypanel.host",
])
# CSRF trusted origins for cross-site requests
# CSRF_TRUSTED_ORIGINS = [
#     "https://whatsapp-1-laundry-2-compose.xqqhik.easypanel.host",
# ]






# ==============================================================================
#  Third-party App Settings
# ==============================================================================

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# ==============================================================================
#  Default
# ==============================================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
SITE_ID = 1




# ✅ Required for django-allauth
SITE_ID = 1
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',  # default
    'allauth.account.auth_backends.AuthenticationBackend',  # allauth
]

# Django-allauth configuration
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
# ACCOUNT_EMAIL_REQUIRED = True
# ACCOUNT_USERNAME_REQUIRED = False
# ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = 'optional'  # Change to 'mandatory' in production






# Social account settings
SOCIALACCOUNT_AUTO_SIGNUP = True
# ACCOUNT_EMAIL_VERIFICATION = "none"
SOCIALACCOUNT_QUERY_EMAIL = True
SOCIALACCOUNT_ADAPTER = 'myapp.adapter.MySocialAccountAdapter'
# SOCIALACCOUNT_ADAPTER = 'users.adapters.CustomSocialAccountAdapter'
ACCOUNT_ADAPTER = 'allauth.account.adapter.DefaultAccountAdapter'



# Configure allauth social providers to avoid SocialApp.DoesNotExist
# SOCIALACCOUNT_PROVIDERS = {
#     'google': {
#         'APP': {
#             'client_id': 'your-client-id',
#             'secret': 'your-secret',
#             'key': ''
#         }
#     }
# }


SITE_URL = 'http://localhost:8000'







# ==============================================================================
#  Email Configuration
# ==============================================================================

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
# EMAIL_HOST = os.getenv("EMAIL_HOST", "mail.vectra.ng")
EMAIL_HOST="mail.vectra.ng" # Hardcoded for now, can be switched to env var if needed
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 465))
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "True") == "True"
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "False") == "True"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "support@vectra.ng")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "Vectra Laundry <support@vectra.ng>")







PAYSTACK_PUBLIC_KEY = os.getenv("PAYSTACK_PUBLIC_KEY")
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")  # ⚠️ REPLACE THIS WITH YOUR SECRET KEY
# PAYSTACK_PAYMENT_AMOUNT = 1550000  # Amount in kobo (e.g., 999 kobo = 9.99 NGN)

# Google Maps API Key
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "YOUR_PLACEHOLDER_KEY")

# ==============================================================================
#  Redis & Celery Configuration
# ==============================================================================

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

import re
# Strip any trailing slash and database number from REDIS_URL so we can cleanly append /0 or /1
base_redis_url = re.sub(r'/[0-9]*$', '', REDIS_URL)

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"{base_redis_url}/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

CELERY_BROKER_URL = f"{base_redis_url}/0"
CELERY_RESULT_BACKEND = f"{base_redis_url}/0"
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE



# CELERY_BROKER_URL = "rediss://default:8824947e9537dcfd047d@147.182.194.8:6380/0?ssl_cert_reqs=CERT_NONE"
# CELERY_RESULT_BACKEND = "rediss://default:8824947e9537dcfd047d@147.182.194.8:6380/0?ssl_cert_reqs=CERT_NONE"

# CELERY_ACCEPT_CONTENT = ['json']
# CELERY_TASK_SERIALIZER = 'json'
# CELERY_RESULT_SERIALIZER = 'json'
# CELERY_TIMEZONE = TIME_ZONE

# # Required SSL options
# CELERY_BROKER_USE_SSL = {
#     "ssl_cert_reqs": "CERT_NONE"   # or CERT_REQUIRED if you have CA certs
# }
# CELERY_RESULT_BACKEND_USE_SSL = {
#     "ssl_cert_reqs": "CERT_NONE"
# }