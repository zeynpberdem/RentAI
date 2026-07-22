"""URL configuration for the RentAI project."""

from django.contrib import admin
from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from reservations.views import ReservationCancelView, ReservationListCreateView
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
    # uuid:pk -> ID'ler artık integer değil UUID (BaseModel'den geliyor).
    path('api/vehicles/<uuid:pk>', VehicleDetailView.as_view(), name='vehicle-detail'),

    # --- Reservations (PDF RES-1/2/3) ---
    path('api/reservations', ReservationListCreateView.as_view(), name='reservation-list-create'),
    path('api/reservations/<uuid:pk>/cancel', ReservationCancelView.as_view(), name='reservation-cancel'),

    # --- API docs (drf-spectacular) — endpoint'leri tarayıcıdan görüp
    # deneyebilmek için; Postman'e gerek kalmadan register/login test edilebilir.
    path('api/schema', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
