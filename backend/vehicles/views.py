"""Views for the vehicle search + admin CRUD API — see PDF GET /api/vehicles, VEH-1."""

from rest_framework import generics, permissions

from users.permissions import IsAdmin

from .filters import VehicleFilter
from .models import Vehicle
from .serializers import VehicleSerializer, VehicleWriteSerializer


class VehicleListView(generics.ListCreateAPIView):
    """
    GET  /api/vehicles -> herkese açık araç arama (VEH-2)
    POST /api/vehicles -> yeni araç ekleme, sadece admin (VEH-1)
    """

    # active_objects: soft-delete edilmiş (is_active=False) araçlar
    # müşteriye açık aramada hiç görünmesin diye bilerek objects yerine
    # bunu kullanıyoruz — admin panel hâlâ objects ile hepsini görebilir.
    queryset = Vehicle.active_objects.select_related("location").order_by("-created_at")
    # select_related("location"): normalde her araç için şubesini ayrı
    # bir sorguyla çekmek gerekirdi (100 araç = 101 sorgu, "N+1 problemi"
    # denen klasik bir performans hatası). select_related, aracı ve
    # şubesini TEK bir sorguda birlikte getiriyor.

    filterset_class = VehicleFilter

    def get_serializer_class(self):
        if self.request.method == "POST":
            return VehicleWriteSerializer
        return VehicleSerializer

    def get_permissions(self):
        # GET (arama) herkese açık kalıyor; POST (yeni araç ekleme) sadece
        # admin. Aynı adres, HTTP metoduna göre farklı izin kuralı.
        if self.request.method == "POST":
            return [IsAdmin()]
        return [permissions.AllowAny()]


class VehicleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET               /api/vehicles/{id} -> herkese açık araç detayı (VEH-3)
    PUT/PATCH/DELETE  /api/vehicles/{id} -> düzenleme/silme, sadece admin (VEH-1)
    """

    queryset = Vehicle.active_objects.select_related("location")

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return VehicleWriteSerializer
        return VehicleSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.AllowAny()]
        return [IsAdmin()]

    def perform_destroy(self, instance):
        # Gerçek silme (DELETE FROM ...) yerine soft-delete: is_active=False
        # yapıyoruz. Böylece bu araca bağlı geçmiş rezervasyon/teslim
        # kayıtları bozulmuyor, sadece araç artık aramada görünmüyor.
        instance.is_active = False
        instance.save()
