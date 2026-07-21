"""Views for user registration — see PDF endpoint POST /api/auth/register."""

from rest_framework import generics, permissions

from .serializers import RegisterSerializer


class RegisterView(generics.CreateAPIView):
    """POST /api/auth/register — creates a new customer account."""

    serializer_class = RegisterSerializer

    # settings.py'daki DEFAULT_PERMISSION_CLASSES = IsAuthenticated kuralının
    # BİLİNÇLİ istisnası: henüz giriş yapmamış biri kayıt olabilmeli,
    # aksi halde hesap açmanın hiçbir yolu olmaz.
    permission_classes = [permissions.AllowAny]