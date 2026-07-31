"""Views for auth/login and driver management — see PDF endpoint POST /api/auth/login."""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, mixins, permissions, viewsets
from rest_framework.filters import OrderingFilter
from rest_framework_simplejwt.views import TokenObtainPairView

from .filters import DriverFilter
from .helpers import Role
from .models import User
from .permissions import IsOperator
from .serializers import (
    DriverCreateSerializer,
    DriverSerializer,
    MeSerializer,
    RoleTokenObtainPairSerializer,
    StaffCreateSerializer,
    StaffSerializer,
)


class RoleTokenObtainPairView(TokenObtainPairView):
    """POST /api/auth/login — access token'ın içine `role` claim'i eklenmiş hali."""

    serializer_class = RoleTokenObtainPairSerializer


class MeView(generics.RetrieveAPIView):
    """GET /api/auth/me — Ayarlar > Hesabım."""

    serializer_class = MeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class StaffViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    GET  /api/auth/staff -> Ayarlar > Personel: diğer operatör hesaplarının listesi
    POST /api/auth/staff -> yeni bir operatör hesabı aç (gerçek şifreyle)
    """

    permission_classes = [IsOperator]
    pagination_class = None

    def get_queryset(self):
        return User.active_objects.filter(role=Role.OPERATOR).order_by("first_name", "last_name")

    def get_serializer_class(self):
        return StaffCreateSerializer if self.action == "create" else StaffSerializer


class DriverViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    GET         /api/auth/drivers      -> operatörün sürücü (müşteri) listesi
    POST        /api/auth/drivers      -> yeni sürücü kaydı aç (şifresiz)
    GET         /api/auth/drivers/{id} -> tek bir sürücünün detayı
    PUT/PATCH   /api/auth/drivers/{id} -> sürücü bilgilerini (TC/ehliyet dahil) düzenle
    DELETE      /api/auth/drivers/{id} -> sürücüyü listeden kaldır (soft-delete)

    Sürücüler artık kendi hesaplarıyla giriş yapmadığı için bu bilgileri
    onlar yerine operatör giriyor/düzenliyor (bkz. DriverCreateSerializer).
    """

    permission_classes = [IsOperator]
    filterset_class = DriverFilter

    # Vehicle/Reservation ile aynı desen: ?ordering=created_at ya da
    # ?ordering=-created_at. Varsayılan sıralama da en yeni kayıt en üstte
    # olacak şekilde -created_at (isim sırası yerine).
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ["created_at"]

    def get_queryset(self):
        return User.active_objects.filter(role=Role.CUSTOMER).order_by("-created_at")

    def get_serializer_class(self):
        return DriverCreateSerializer if self.action == "create" else DriverSerializer

    def perform_destroy(self, instance):
        # Vehicle.perform_destroy ile aynı desen: gerçek silme yerine
        # is_active=False — sürücüye bağlı geçmiş rezervasyon kayıtları bozulmasın.
        instance.is_active = False
        instance.save()
