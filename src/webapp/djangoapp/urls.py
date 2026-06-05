"""
URL configuration for djangoapp project.

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

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from djangoapp.user_interface.views import SessionLoginView, SessionLogoutView

admin_title = f"{settings.PRODUCT_DISPLAY_NAME} - Administration"
admin.site.site_header = admin_title
admin.site.site_title = admin_title

urlpatterns = [
    path("", include("djangoapp.user_interface.urls")),
    path("accounts/login/", SessionLoginView.as_view(), name="login"),
    path("accounts/logout/", SessionLogoutView.as_view(), name="logout"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("admin/", admin.site.urls),
    path("api/", include("djangoapp.rest_api.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
