"""
URL configuration for stockwise_py project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve as static_serve
from core.views import safe_media_serve
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('qr/', include('stockwise_qr.qrstock.urls')),
    path('', include('core.urls')),
]

# Serve media in local/dev environments even if DEBUG is false
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# Extra fallback for media serving to prevent 404s in non-debug environments
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', safe_media_serve),
    re_path(r'^Media/(?P<path>.*)$', safe_media_serve),
    re_path(r'^MEDIA/(?P<path>.*)$', safe_media_serve),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
