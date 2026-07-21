"""
URL configuration for config project.

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
from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from users.views import RegisterView
from vehicles.views import VehicleDetailView, VehicleListView

urlpatterns = [
    path('admin/', admin.site.urls),

    # --- Auth (PDF: POST /api/auth/register · /login · /refresh) ---
    path('api/auth/register', RegisterView.as_view(), name='auth-register'),
    # TokenObtainPairView: email+password alır, {access, refresh} döner.
    path('api/auth/login', TokenObtainPairView.as_view(), name='auth-login'),
    # TokenRefreshView: eski refresh token'dan yeni access token üretir.
    path('api/auth/refresh', TokenRefreshView.as_view(), name='auth-refresh'),

    # --- Vehicles (PDF VEH-2: GET /api/vehicles, filtre + sayfalama) ---
    path('api/vehicles', VehicleListView.as_view(), name='vehicle-list'),
    # --- Vehicle detail (PDF VEH-3) ---
    path('api/vehicles/<int:pk>', VehicleDetailView.as_view(), name='vehicle-detail'),

    # --- API docs (drf-spectacular) — endpoint'leri tarayıcıdan görüp
    # deneyebilmek için; Postman'e gerek kalmadan register/login test edilebilir.
    path('api/schema', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
