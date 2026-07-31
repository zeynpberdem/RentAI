"""Views for the vehicle search + admin CRUD API — see PDF GET /api/vehicles, VEH-1."""

from django.db.models import Prefetch
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter

from reservations.models import Reservation
from users.permissions import IsAdmin, IsOperator

from .filters import VehicleFilter
from .models import Location, Vehicle
from .serializers import (
    LocationSerializer,
    VehicleCalendarSerializer,
    VehicleSerializer,
    VehicleStaffSerializer,
    VehicleWriteSerializer,
)


class LocationListView(generics.ListAPIView):
    """GET /api/locations — şube listesi, arama ekranındaki şube seçimi için."""

    queryset = Location.active_objects.order_by("city", "name")
    serializer_class = LocationSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None  # şube sayısı az, sayfalamaya gerek yok


class VehicleViewSet(viewsets.ModelViewSet):
    """
    GET               /api/vehicles       -> herkese açık araç arama (VEH-2)
    POST              /api/vehicles       -> yeni araç ekleme, sadece admin (VEH-1)
    GET               /api/vehicles/{id}  -> herkese açık araç detayı (VEH-3)
    PUT/PATCH/DELETE  /api/vehicles/{id}  -> düzenleme/silme, sadece admin (VEH-1)
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

    # Global ayardaki DjangoFilterBackend'e ek olarak OrderingFilter'ı da
    # açıyoruz — ?ordering=daily_price ya da ?ordering=-daily_price gibi.
    # Sadece bu alanla sınırlıyoruz (ordering_fields): araç listesinde
    # anlamlı tek sıralama kriteri bu, keyfi bir alanla (ör. plaka)
    # sıralamaya izin vermek şimdilik gereksiz.
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ["daily_price"]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return VehicleWriteSerializer
        # Operatör/admin plakayı da görebilir (fiziksel aracı tanımak için
        # gerekli) — herkese açık müşteri aramasında (AllowAny) plaka yok.
        if self.request.user.is_authenticated and self.request.user.role in ("operator", "admin"):
            return VehicleStaffSerializer
        return VehicleSerializer

    def get_permissions(self):
        # list/retrieve (arama, detay) herkese açık. Yeni araç ekleme (create)
        # hâlâ sadece admin'de — ama günlük düzenleme/soft-delete (bir yanlışlık
        # olursa düzeltme/kaldırma) artık operatörün de işi, bu yüzden
        # update/destroy'da IsOperator'ı da kabul ediyoruz.
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
        if self.action == "create":
            return [IsAdmin()]
        return [(IsAdmin | IsOperator)()]

    def perform_destroy(self, instance):
        # Gerçek silme (DELETE FROM ...) yerine soft-delete: is_active=False
        # yapıyoruz. Böylece bu araca bağlı geçmiş rezervasyon/teslim
        # kayıtları bozulmuyor, sadece araç artık aramada görünmüyor.
        instance.is_active = False
        instance.save()

    @action(detail=False, methods=["get"])
    def calendar(self, request):
        """GET /api/vehicles/calendar?start_date=&end_date= — Rezervasyon
        Takvimi ekranı için: her aracı, verilen tarih aralığıyla kesişen
        rezervasyonlarıyla birlikte TEK istekte döner.

        Bundan önce frontend hem /vehicles hem /reservations'ı ayrı ayrı
        çekip "hangi rezervasyon hangi araca ait" eşleştirmesini kendi
        (JS içinde) yapıyordu — üstelik /reservations zaten her rezervasyonun
        içine aracın TAM halini gömdüğü için araç bilgisi ağdan iki kere
        taşınıyordu. Bu action, join'i veritabanı seviyesinde (prefetch)
        yapıp aracı SADECE bir kere döndürür.

        Ayrıca normal /vehicles listesiyle aynı filtreleri (şube/segment/
        durum) ve sayfalamayı miras alır (filterset_class + get_queryset
        VehicleViewSet'ten geliyor) — filo büyüdükçe burası da Araçlar
        ekranındaki gibi daraltılabilir.
        """
        reservations_qs = Reservation.active_objects.select_related("customer")

        start = request.query_params.get("start_date")
        end = request.query_params.get("end_date")
        # Çakışma formülü: rezervasyon.start < aralık.end VE rezervasyon.end > aralık.start
        if end:
            reservations_qs = reservations_qs.filter(start_date__lt=end)
        if start:
            reservations_qs = reservations_qs.filter(end_date__gt=start)

        queryset = self.filter_queryset(self.get_queryset()).prefetch_related(
            Prefetch("reservations", queryset=reservations_qs, to_attr="calendar_reservations")
        )

        page = self.paginate_queryset(queryset)
        serializer = VehicleCalendarSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)
