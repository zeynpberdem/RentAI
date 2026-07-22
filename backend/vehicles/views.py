"""Views for the public vehicle search API — see PDF GET /api/vehicles."""

from rest_framework import generics, permissions

from .filters import VehicleFilter
from .models import Vehicle
from .serializers import VehicleSerializer


class VehicleListView(generics.ListAPIView):
    """GET /api/vehicles — searchable/filterable vehicle listing."""

    # active_objects: soft-delete edilmiş (is_active=False) araçlar
    # müşteriye açık aramada hiç görünmesin diye bilerek objects yerine
    # bunu kullanıyoruz — admin panel hâlâ objects ile hepsini görebilir.
    queryset = Vehicle.active_objects.select_related("location").order_by("-created_at")
    # select_related("location"): normalde her araç için şubesini ayrı
    # bir sorguyla çekmek gerekirdi (100 araç = 101 sorgu, "N+1 problemi"
    # denen klasik bir performans hatası). select_related, aracı ve
    # şubesini TEK bir sorguda birlikte getiriyor.

    serializer_class = VehicleSerializer
    filterset_class = VehicleFilter

    # settings.py'daki DEFAULT_PERMISSION_CLASSES = IsAuthenticated
    # kuralının bilinçli istisnası: araç aramak için giriş yapmış olmak
    # gerekmiyor, tıpkı gerçek bir kiralama sitesinde olduğu gibi.
    permission_classes = [permissions.AllowAny]


class VehicleDetailView(generics.RetrieveAPIView):
    """GET /api/vehicles/{id} — single vehicle detail (PDF VEH-3)."""

    # Liste view'ıyla aynı sebep: silinmiş bir aracın detayına da müşteri
    # erişemesin.
    queryset = Vehicle.active_objects.select_related("location")
    serializer_class = VehicleSerializer

    # Liste sayfasıyla aynı mantık: detay sayfasına bakmak için de
    # giriş yapmış olmak gerekmiyor.
    permission_classes = [permissions.AllowAny]
