"""Views for user registration — see PDF endpoint POST /api/auth/register."""

from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import RegisterSerializer, RoleTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    """POST /api/auth/register — creates a new customer account."""

    serializer_class = RegisterSerializer

    # settings.py'daki DEFAULT_PERMISSION_CLASSES = IsAuthenticated kuralının
    # BİLİNÇLİ istisnası: henüz giriş yapmamış biri kayıt olabilmeli,
    # aksi halde hesap açmanın hiçbir yolu olmaz.
    permission_classes = [permissions.AllowAny]


class RoleTokenObtainPairView(TokenObtainPairView):
    """POST /api/auth/login — access token'ın içine `role` claim'i eklenmiş hali."""

    serializer_class = RoleTokenObtainPairSerializer