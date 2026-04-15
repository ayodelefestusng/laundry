"""
URL configuration for myproject project.
"""
from django.contrib import admin
from django.urls import path, include
from django.urls import path
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('admin/', admin.site.urls),
    # path('accounts/', include('django.contrib.auth.urls')),
    path('', include('myapp.urls')),
    path('', include('django.contrib.auth.urls')),  # Built-in login/logout/password views
    path('accounts/', include('allauth.urls')),              # ✅ Social login (Google, Facebook, etc.)

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)