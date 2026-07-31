"""Handover model — see PDF section 3.4 (Handover) and HND-1/HND-2."""

from django.db import models

from core.models import BaseModel
from reservations.models import Reservation

from .helpers import Type


class Handover(BaseModel):
    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.PROTECT,
        related_name="handovers",
    )
    type = models.CharField(max_length=40, choices=Type.choices)
    odometer_km = models.PositiveIntegerField()
    fuel_level = models.PositiveSmallIntegerField()  # yüzde, 0-100
    damage_notes = models.TextField(blank=True)

    # Sadece iade (return) kaydında doldurulur; teslimde her zaman 0.
    extra_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = "handovers"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.reservation_id} — {self.type}"