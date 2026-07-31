"""Auth uc noktalari — see PDF POST /login · /refresh.

config/urls.py'de 'api/auth/' prefix'iyle include ediliyor.
"""

from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import DriverViewSet, MeView, RoleTokenObtainPairView, StaffViewSet

# trailing_slash=False: projedeki hicbir uc noktada sonda '/' yok.
router = DefaultRouter(trailing_slash=False)
router.register('drivers', DriverViewSet, basename='driver')
router.register('staff', StaffViewSet, basename='staff')

urlpatterns = [
    # RoleTokenObtainPairView: email+password alır, {access, refresh} döner;
    # access token'ın içine ayrıca kullanıcının rolü gömülür.
    path('login', RoleTokenObtainPairView.as_view(), name='auth-login'),
    path('refresh', TokenRefreshView.as_view(), name='auth-refresh'),
    # GET: kendi hesap bilgilerini gör (Ayarlar > Hesabım).
    path('me', MeView.as_view(), name='auth-me'),
] + router.urls
