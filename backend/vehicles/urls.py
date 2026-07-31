"""Vehicles/locations uc noktalari — see PDF VEH-1/2/3.

config/urls.py'de 'api/' prefix'iyle include ediliyor (bu yuzden path'ler
kendi 'locations'/'vehicles' onekini burada tasiyor).
"""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import LocationListView, VehicleViewSet

# trailing_slash=False: projedeki hicbir uc noktada sonda '/' yok
# (ornegin 'api/vehicles', 'api/vehicles/' degil) — router'in urettigi
# adreslerin de bu yerlesik kurala uymasi icin.
router = DefaultRouter(trailing_slash=False)
router.register('vehicles', VehicleViewSet, basename='vehicle')

urlpatterns = [
    # --- Locations (arama ekranındaki şube seçimi için) ---
    path('locations', LocationListView.as_view(), name='location-list'),
] + router.urls
