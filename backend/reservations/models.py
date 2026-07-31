"""Reservation model — see PDF section 3.3 (Reservation) and RES-1/2/3."""

from django.conf import settings
from django.db import models

from core.models import BaseModel
from vehicles.models import Location, Vehicle

from .helpers import ReservationSource, ReservationType, Status


class Reservation(BaseModel):
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reservations",
    )
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.PROTECT,
        related_name="reservations",
    )
    # DateTimeField (DateField DEĞİL): teslim/iade saati de tutuluyor — bkz.
    # Rezervasyon Listesi ekranındaki "24.07.2026 14:37" gibi gösterim.
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    # PositiveSmallIntegerField (CharField DEĞİL): Hacer Hanım'ın istediği
    # sayısal durum kodları (1/2/3/4/99) — bkz. helpers.Status.
    status = models.PositiveSmallIntegerField(
        choices=Status.choices,
        default=Status.PENDING,
    )
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    # Süre Uzat işlemi yapıldıysa doldurulur — Rezervasyon Listesi'nde
    # tutarın yanına "+" göstermek için (bkz. ReservationViewSet.extend).
    extended_at = models.DateTimeField(null=True, blank=True)
    # İptal edildiyse NE ZAMAN edildiği — "Rezervasyon Geçmişi" (yaşam
    # döngüsü) görünümünde göstermek için (bkz. ReservationViewSet.cancel).
    cancelled_at = models.DateTimeField(null=True, blank=True)

    type = models.CharField(
        max_length=20,
        choices=ReservationType.choices,
        default=ReservationType.SHORT_TERM,
    )
    source = models.CharField(
        max_length=20,
        choices=ReservationSource.choices,
        default=ReservationSource.BRANCH,
    )

    # Genelde ikisi de aracın bulunduğu şubedir (bkz. serializer'daki varsayılan
    # atama), ama farklı bir yerden teslim/farklı bir yere iade mümkün olsun
    # diye ayrı ayrı tutuluyor — bkz. Ziraat Filo'daki "Teslim Alma/Etme Ofisi".
    pickup_location = models.ForeignKey(
        Location,
        on_delete=models.PROTECT,
        related_name="pickup_reservations",
        null=True,
        blank=True,
    )
    return_location = models.ForeignKey(
        Location,
        on_delete=models.PROTECT,
        related_name="return_reservations",
        null=True,
        blank=True,
    )

    # Fiyatın nasıl hesaplandığının kaydı (günlük fiyat, gün sayısı, toplam).
    # Şimdilik basit; ileride sezon/indirim kuralları eklenince bu alan
    # zaten hazır olacak, model değişmeyecek.
    pricing_snapshot = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "reservations"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.customer.email} — {self.vehicle.plate} ({self.start_date} → {self.end_date})"
