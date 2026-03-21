"""
Django settings for myproject project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

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
]

# ==============================================================================
#  Application Definition
# ==============================================================================

INSTALLED_APPS = [
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

    # My apps
    'myapp', # Correct app name

  'django_bootstrap5',
    # 'htmx_messages',
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
    "myapp.tenant_middleware.TenantMiddleware"
]

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
            ],
        },
    },
]

WSGI_APPLICATION = 'myproject.wsgi.application'

# ==============================================================================
#  Database & Auth
# ==============================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# AUTH_USER_MODEL = 'myapp.CustomUser' # Correct user model reference
AUTH_USER_MODEL = 'myapp.CustomUser'


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'login'
LOGIN_URL = 'login'

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

# ==============================================================================
#  Email Configuration
# ==============================================================================

# EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
# EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
# EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
# EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True") == "True"
# EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
# EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
# DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL")


CSRF_TRUSTED_ORIGINS = [
    "https://9415-105-113-69-195.ngrok-free.app",
]



EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'mail.dignityconcept.tech'
EMAIL_PORT = 465
EMAIL_USE_TLS = False
EMAIL_USE_SSL = True
EMAIL_HOST_USER = 'solutions@dignityconcept.tech'
EMAIL_HOST_PASSWORD = 'd~Gg@KKEUm-_QVw~'
DEFAULT_FROM_EMAIL = 'Dignity Concept <solutions@dignityconcept.tech>'


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

STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
# Base URL of your application, used for absolute URL generation.
# Replace with your actual domain when deploying.
SITE_URL = 'http://localhost:8000'



# settings.py
# ... other settings

# PayPal API Settings


# Use 'https://api.sandbox.paypal.com' for testing
# Use 'https://api.paypal.com' for production
PAYPAL_BASE_URL = 'https://api.sandbox.paypal.com'
PAYPAL_MODE = 'sandbox' # Use 'live' for production
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")

# Base URL of your application, used for absolute URL generation.
SITE_URL = 'http://localhost:8000'



PAYSTACK_PUBLIC_KEY = 'pk_live_658eac33a92a6e21bb80a7cdbb140d9a2588a88e'
PAYSTACK_SECRET_KEY = 'sk_live_3fc94a5e6963df90db0efd10bc51cd3bc0cb526d'  # ⚠️ REPLACE THIS WITH YOUR SECRET KEY
# PAYSTACK_PAYMENT_AMOUNT = 1550000  # Amount in kobo (e.g., 999 kobo = 9.99 NGN)
