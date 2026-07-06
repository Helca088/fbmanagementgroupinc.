"""
URL configuration for ticketsystem project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include('tickets.urls')),
    path("", include("pwa.urls")),
    path('admin-sw.js', TemplateView.as_view(
        template_name="tickets/sw/admin-sw.js",
        content_type="application/javascript"
    ), name="admin_sw"),
    path('employee-sw.js', TemplateView.as_view(
        template_name="tickets/sw/employee-sw.js",
        content_type="application/javascript"
    ), name="employee_sw"),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
