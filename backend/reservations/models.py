"""Reservation model — see PDF section 3.3 (Reservation) and RES-1/2/3."""

from django.conf import settings
from django.db import models

from core.models import BaseModel
from vehicles.models import Vehicle

from .helpers import Status


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
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    # Fiyatın nasıl hesaplandığının kaydı (günlük fiyat, gün sayısı, toplam).
    # Şimdilik basit; ileride sezon/indirim kuralları eklenince bu alan
    # zaten hazır olacak, model değişmeyecek.
    pricing_snapshot = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "reservations"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.customer.email} — {self.vehicle.plate} ({self.start_date} → {self.end_date})"
