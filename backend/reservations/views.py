"""Views for reservations — see PDF RES-1/2/3."""

from datetime import timedelta

from django.db.models import Case, DateTimeField, F, IntegerField, Value, When
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
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

# Hacer Hanım'ın kuralı: planlanan teslim saatinden (start_date) bu kadar
# saat geçtiği hâlde araç hâlâ Teslim Bekliyor'da kalmışsa, müşteri
# gelmemiş (no-show) sayılır ve rezervasyon otomatik iptal edilir — aksi
# halde araç, gelmeyecek bir müşteri için süresiz bloke kalırdı.
NO_SHOW_GRACE_HOURS = 6


def cancel_noshow_reservations():
    # Projede Celery/cron kurulu değil (bkz. PDF: "opsiyonel, zaman
    # kalırsa") — bu yüzden zamanlanmış bir görev yerine, liste her
    # çekildiğinde (get_queryset) tembel (lazy) olarak çalıştırılıyor.
    # .update(): tek sorguda toplu güncelleme, save()/sinyal tetiklemiyor
    # — bu durumda ihtiyaç da yok, Vehicle.status zaten sadece teslim
    # (delivery) anında değişiyor, Teslim Bekliyor aşamasında hiç dokunulmamıştı.
    cutoff = timezone.now() - timedelta(hours=NO_SHOW_GRACE_HOURS)
    Reservation.active_objects.filter(status=Status.CONFIRMED, start_date__lt=cutoff).update(
        status=Status.CANCELLED, cancelled_at=timezone.now()
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
        cancel_noshow_reservations()

        # prefetch_related("handovers"): ReservationSerializer.get_is_early_return
        # her rezervasyon için handover kayıtlarına bakıyor — prefetch olmadan
        # bu N+1 sorguya (liste başına bir sorgu daha) yol açardı.
        #
        # Varsayılan sıralama üç öncelik katmanına ayrılıyor (Hacer Hanım'ın
        # isteği): 1) Kirada olanlar en üstte, iadesi en yakın olan önce —
        # operatörün en çok takip etmesi gereken, dışarıda gezen araçlar.
        # 2) 2 gün içinde teslim alınacak (Teslim Bekliyor) rezervasyonlar,
        # teslimi en yakın olan önce — operatör hazırlık yapabilsin.
        # 3) Geri kalan her şey, SIPP koduna göre (az önceki mantık).
        soon_cutoff = timezone.now() + timedelta(days=2)
        priority = Case(
            When(status=Status.ACTIVE, then=Value(0)),
            When(status=Status.CONFIRMED, start_date__lte=soon_cutoff, then=Value(1)),
            default=Value(2),
            output_field=IntegerField(),
        )
        # Katman 0 iadeye, katman 1 teslime göre sıralanıyor; katman 2'de
        # bu alan hep NULL kalıp SIPP koduna devrediyor.
        sort_date = Case(
            When(status=Status.ACTIVE, then=F("end_date")),
            When(status=Status.CONFIRMED, start_date__lte=soon_cutoff, then=F("start_date")),
            default=Value(None),
            output_field=DateTimeField(null=True),
        )

        queryset = (
            Reservation.active_objects.select_related(
                "vehicle", "vehicle__location", "customer", "pickup_location", "return_location"
            )
            .prefetch_related("handovers")
            .annotate(priority=priority, sort_date=sort_date)
            .order_by("priority", "sort_date", "vehicle__sipp_code", "vehicle__plate", "-created_at")
        )
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
        # timezone.localtime(...): reservation.start_date DB'den UTC olarak
        # geliyor, new_end_date ise istekten yeni ayrıştırıldığı için zaten
        # yerel (Europe/Istanbul) — ikisini aynı takvim gününe göre
        # kıyaslamak için ikisini de yerel saate çeviriyoruz (bkz.
        # handovers/serializers.py'deki aynı desen).
        days = max(
            (timezone.localtime(new_end_date).date() - timezone.localtime(reservation.start_date).date()).days,
            1,
        )
        total_price = reservation.vehicle.daily_price * days

        # extension_amount: bu uzatmayla eklenen fark — Rezervasyon
        # Listesi'nde "+" işaretinin yanında TAM tutar yerine sadece bu
        # farkın gösterilmesi için (bkz. ReservationSerializer). Birden
        # fazla uzatma yapılırsa üst üste birikir.
        reservation.extension_amount += total_price - reservation.total_price

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
