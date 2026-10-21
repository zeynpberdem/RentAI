"""Views for the vehicle search + admin CRUD API — see PDF GET /api/vehicles, VEH-1."""

import hashlib
import math
import time
from datetime import timedelta

from django.db.models import Case, Exists, IntegerField, OuterRef, Prefetch, Value, When
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from reservations.helpers import Status as ReservationStatus
from reservations.models import Reservation
from users.permissions import IsAdmin, IsOperator
from vehicles.helpers import Status as VehicleStatus

from .filters import VehicleFilter
from .models import Location, SippRate, Vehicle
from .serializers import (
    LocationSerializer,
    SippRateSerializer,
    VehicleCalendarSerializer,
    VehicleSerializer,
    VehicleStaffSerializer,
    VehicleWriteSerializer,
)

# Canlı Takip ekranındaki simülasyon için — gerçek GPS yok, sadece kirada
# olan araçları şubelerinin etrafında yavaşça döndürüyoruz (bkz.
# VehicleViewSet.live_positions). LOOP_SECONDS: bir tam turu kaç saniyede
# tamamlar (uzun tutuldu ki her 5 saniyelik polling'de sadece hafifçe
# ilerlesin, sıçramasın). RADIUS_DEGREES: BİLEREK küçük (~200-250m) —
# gerçek kıyı/harita verisi yok, büyük bir yarıçap sahil kenarındaki
# şubelerde (ör. Kadıköy) rastgele yön denize denk gelip aracı deniz
# üzerinde gösterebiliyordu. Küçük tutmak riski azaltıyor (garanti etmiyor).
LIVE_POSITION_LOOP_SECONDS = 180
LIVE_POSITION_RADIUS_DEGREES = 0.0025


class LocationListView(generics.ListAPIView):
    """GET /api/locations — şube listesi, arama ekranındaki şube seçimi için."""

    queryset = Location.active_objects.order_by("city", "name")
    serializer_class = LocationSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None  # şube sayısı az, sayfalamaya gerek yok


class VehicleViewSet(viewsets.ModelViewSet):
    """
    GET               /api/vehicles       -> herkese açık araç arama (VEH-2)
    POST              /api/vehicles       -> yeni araç ekleme, admin/operatör (VEH-1)
    GET               /api/vehicles/{id}  -> herkese açık araç detayı (VEH-3)
    PUT/PATCH/DELETE  /api/vehicles/{id}  -> düzenleme/silme, admin/operatör (VEH-1)
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
        # list/retrieve (arama, detay) herkese açık. create/update/destroy
        # (filoya araç ekleme, günlük düzenleme, soft-delete) operatörün de
        # işi — hepsinde IsOperator'ı da kabul ediyoruz.
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
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

        # Araç sırasında öncelik (Hacer Hanım'ın isteği, Rezervasyon
        # Listesi'ndeki ile aynı mantık): 1) şu an kirada olan araçlar önce,
        # 2) 2 gün içinde teslim alınacak (Teslim Bekliyor) rezervasyonu
        # olan araçlar sonra, 3) geri kalanı SIPP koduna göre.
        soon_cutoff = timezone.now() + timedelta(days=2)
        upcoming_confirmed = Reservation.active_objects.filter(
            vehicle=OuterRef("pk"), status=ReservationStatus.CONFIRMED, start_date__lte=soon_cutoff
        )
        priority = Case(
            When(status=VehicleStatus.RENTED, then=Value(0)),
            When(Exists(upcoming_confirmed), then=Value(1)),
            default=Value(2),
            output_field=IntegerField(),
        )

        # DİKKAT: VehicleFilter.start_date/end_date, normal /vehicles
        # aramasında "bu tarih aralığında MÜSAİT araçları getir" anlamına
        # geliyor (VEH-2) — yani rezervasyonlu/kirada araçları SONUÇTAN
        # ÇIKARIYOR. Takvim'in start_date/end_date'i ise "hangi haftayı
        # görüntülüyorum" demek — aynı parametre adı, tamamen farklı amaç.
        # self.filter_queryset() kullanırsak ikisi çakışır ve tam da
        # göstermek istediğimiz kirada/dolu araçlar filtrelenip kaybolur.
        # Bu yüzden VehicleFilter'ı burada elle, bu iki alan olmadan çalıştırıyoruz.
        filter_params = request.query_params.copy()
        filter_params.pop("start_date", None)
        filter_params.pop("end_date", None)
        filtered_queryset = VehicleFilter(filter_params, queryset=self.get_queryset(), request=request).qs

        queryset = (
            filtered_queryset.annotate(priority=priority)
            .order_by("priority", "sipp_code", "plate")
            .prefetch_related(
                Prefetch("reservations", queryset=reservations_qs, to_attr="calendar_reservations")
            )
        )

        page = self.paginate_queryset(queryset)
        serializer = VehicleCalendarSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=["get"], url_path="live-positions")
    def live_positions(self, request):
        """GET /api/vehicles/live-positions — Canlı Takip ekranı için SADECE
        kirada olan araçların simüle edilmiş konumu. Gerçek GPS yok, hiçbir
        şey veritabanına yazılmıyor — her istekte o anki sunucu saatine göre
        aracın şubesi etrafında yavaşça dönen deterministik bir nokta
        hesaplanır. Frontend bunu birkaç saniyede bir polling ile çekip
        marker'ı kaydırır (bkz. FleetLiveMapView.vue).
        """
        vehicles = Vehicle.active_objects.filter(
            status=VehicleStatus.RENTED,
            location__latitude__isnull=False,
            location__longitude__isnull=False,
        ).select_related("location")

        now = time.time()
        positions = []
        for vehicle in vehicles:
            # UUID'den sabit bir başlangıç açısı türetiyoruz — aksi halde
            # her araç aynı anda aynı açıda olur, hepsi birlikte "senkron"
            # hareket ediyormuş gibi görünürdü.
            phase = (int(hashlib.md5(str(vehicle.id).encode()).hexdigest(), 16) % 360) * (math.pi / 180)
            angle = phase + now * (2 * math.pi / LIVE_POSITION_LOOP_SECONDS)
            positions.append({
                "id": str(vehicle.id),
                "lat": vehicle.location.latitude + LIVE_POSITION_RADIUS_DEGREES * math.sin(angle),
                "lng": vehicle.location.longitude + LIVE_POSITION_RADIUS_DEGREES * math.cos(angle),
            })
        return Response(positions)


class SippRateViewSet(viewsets.ModelViewSet):
    """
    GET               /api/sipp-rates      -> SIPP Fiyat Tablosu listesi
    POST              /api/sipp-rates      -> yeni SIPP kodu + fiyat ekle
    PUT/PATCH/DELETE  /api/sipp-rates/{id} -> fiyat güncelle/kodu kaldır

    Bir fiyat güncellendiğinde, o SIPP kodundaki TÜM araçların daily_price'ı
    da toplu güncellenir (bkz. perform_update) — Hacer Hanım'ın "araçlar
    SIPP koduna göre fiyatlansın" isteğinin can alıcı kısmı burası.
    """

    queryset = SippRate.active_objects.all()
    serializer_class = SippRateSerializer
    permission_classes = [IsAdmin | IsOperator]
    pagination_class = None  # SIPP kodu sayısı az (ACRISS standardı sabit), sayfalamaya gerek yok

    def perform_update(self, serializer):
        rate = serializer.save()
        Vehicle.active_objects.filter(sipp_code=rate.sipp_code).update(daily_price=rate.daily_price)
