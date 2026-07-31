"""Views for reservations — see PDF RES-1/2/3."""

from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from users.permissions import IsCustomer, IsOperator

from .filters import ReservationFilter
from .helpers import Status
from .models import Reservation
from .serializers import (
    ReservationCreateSerializer,
    ReservationExtendSerializer,
    ReservationSerializer,
    ReservationStaffCreateSerializer,
)


class ReservationViewSet(viewsets.ModelViewSet):
    """
    GET  /api/reservations              -> müşteri KENDİ rezervasyonlarını (RES-3),
                                            operatör TÜM rezervasyonları görür (teslim/iade
                                            kaydı açarken doğru rezervasyonu bulabilsin diye).
    POST /api/reservations              -> müşteri kendi adına (RES-1), operatör ise
                                            seçtiği bir sürücü (müşteri) adına rezervasyon açar
                                            (bkz. "Sürücüler" ekranı).
    POST /api/reservations/{id}/cancel  -> kendi rezervasyonunu iptal et (RES-2)

    Sadece list/create/cancel var — retrieve/update/destroy bilerek yok,
    çünkü PDF'in istediği rezervasyon işlemleri bunlardan ibaret (bir
    rezervasyon elle güncellenmez ya da silinmez, sadece iptal edilir).
    """

    # RES-3: ?status=cancelled gibi bir sorgu parametresiyle filtreleme +
    # arama (?search=) + tarih aralığı (?start_date_from=&start_date_to=).
    filterset_class = ReservationFilter

    # Teslim/İade tarihi sütunlarının başlığına tıklayınca sıralama +
    # "İade Alınacak Listesi" gibi ekranlar için ?ordering=end_date.
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ["start_date", "end_date"]

    def get_permissions(self):
        # Oluşturma hem müşterinin hem operatörün işi olabilir (operatör bir
        # sürücü adına rezervasyon açabilir — bkz. "Sürücüler" ekranı).
        # İptal ise sadece müşterinin kendi işi (bkz. cancel action'ın
        # permission_classes'ı).
        return [(IsCustomer | IsOperator)()]

    def get_serializer_class(self):
        # Okuma (liste) ve yazma (oluşturma) için farklı serializer kullanıyoruz:
        # okumada araç bilgisini tam gösteriyoruz, yazmada araç id'si + tarih
        # yeterli — operatör ayrıca "customer" (sürücü) alanını da gönderir.
        if self.action == "create":
            if self.request.user.role == "operator":
                return ReservationStaffCreateSerializer
            return ReservationCreateSerializer
        return ReservationSerializer

    def get_queryset(self):
        # prefetch_related("handovers"): ReservationSerializer.get_is_early_return
        # her rezervasyon için handover kayıtlarına bakıyor — prefetch olmadan
        # bu N+1 sorguya (liste başına bir sorgu daha) yol açardı.
        queryset = Reservation.active_objects.select_related(
            "vehicle", "vehicle__location", "customer", "pickup_location", "return_location"
        ).prefetch_related("handovers")
        if self.request.user.role == "operator":
            return queryset
        return queryset.filter(customer=self.request.user)

    def perform_create(self, serializer):
        if self.request.user.role == "operator":
            # customer, ReservationStaffCreateSerializer'ın "customer"
            # alanından zaten validated_data içinde geliyor.
            serializer.save()
        else:
            # customer, istekte gönderilmez — her zaman giriş yapmış
            # kullanıcının kendisi olur, başkası adına açamaz.
            serializer.save(customer=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[IsCustomer])
    def cancel(self, request, pk=None):
        # get_object(): get_queryset() zaten müşteriyi kendi rezervasyonlarıyla
        # sınırlıyor, bu yüzden başkasının rezervasyon ID'sini denerse "yok"
        # (404) döner — "var ama senin değil" (403) demek, o rezervasyonun
        # varlığını ifşa eder, bu yüzden 404 tercih ediliyor.
        reservation = self.get_object()

        # Hacer Hanım'ın kuralı: sadece Onay Bekliyor ya da Teslim Bekliyor
        # durumundayken iptal edilebilir — araç bir kere kiraya (ACTIVE)
        # çıktıktan sonra ARTIK iptal edilemez (zaten iptal/tamamlanmış
        # olanlar da bu ikisinin dışında kaldığı için ayrıca kontrol gerekmiyor).
        if reservation.status not in (Status.PENDING, Status.CONFIRMED):
            return Response(
                {"detail": "Bu rezervasyon sadece Onay Bekliyor ya da Teslim Bekliyor durumundayken iptal edilebilir."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reservation.status = Status.CANCELLED
        reservation.cancelled_at = timezone.now()
        reservation.save()
        return Response(ReservationSerializer(reservation).data)

    @action(detail=True, methods=["post"], permission_classes=[IsOperator])
    def extend(self, request, pk=None):
        """POST /api/reservations/{id}/extend — Rezervasyon Listesi'ndeki
        "Süre Uzat" satır aksiyonu. Sadece devam eden/henüz başlamamış bir
        rezervasyonun bitiş tarihini ileri alır, fiyatı yeniden hesaplar ve
        extended_at'ı işaretler (bkz. ReservationSerializer.get_is_extended)."""
        reservation = self.get_object()

        if reservation.status not in (Status.PENDING, Status.CONFIRMED, Status.ACTIVE):
            return Response(
                {"detail": "Bu rezervasyon uzatılabilir bir durumda değil."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ReservationExtendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_end_date = serializer.validated_data["end_date"]

        if new_end_date <= reservation.end_date:
            return Response(
                {"detail": "Yeni bitiş tarihi, mevcut bitiş tarihinden sonra olmalı."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Çakışma kontrolü: sadece UZAYAN kısım (eski bitiş -> yeni bitiş)
        # başka bir rezervasyonla çakışıyor mu — [start, eski_end] zaten
        # sorunsuz geçerliydi, tekrar kontrol etmeye gerek yok.
        conflicting = (
            Reservation.objects.filter(
                vehicle=reservation.vehicle,
                start_date__lt=new_end_date,
                end_date__gt=reservation.end_date,
            )
            .exclude(pk=reservation.pk)
            .exclude(status__in=[Status.CANCELLED, Status.COMPLETED])
        )
        if conflicting.exists():
            return Response(
                {"detail": "Araç, uzatmak istediğin tarih aralığında müsait değil."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # create()'teki aynı max(...,1) kuralı — bkz. ReservationCreateSerializer.create.
        days = max((new_end_date.date() - reservation.start_date.date()).days, 1)
        total_price = reservation.vehicle.daily_price * days

        reservation.end_date = new_end_date
        reservation.total_price = total_price
        reservation.pricing_snapshot = {
            "daily_price": str(reservation.vehicle.daily_price),
            "days": days,
            "total_price": str(total_price),
        }
        reservation.extended_at = timezone.now()
        reservation.save()
        return Response(ReservationSerializer(reservation).data)
