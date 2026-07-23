"""ServiceRequest model — see PDF section 3.5 and SRV-1/SRV-2."""

from django.conf import settings
from django.db import models

from core.models import BaseModel
from vehicles.models import Vehicle


class ServiceRequest(BaseModel):
    class RequestType(models.TextChoices):
        MAINTENANCE = "maintenance", "Maintenance"  # Bakım
        SERVICE = "service", "Service"                # Servis
        WASH = "wash", "Wash"                          # Yıkama

    class Priority(models.TextChoices):
        LOW = "low", "Low"          # Düşük
        NORMAL = "normal", "Normal"
        HIGH = "high", "High"       # Yüksek

    class Status(models.TextChoices):
        OPEN = "open", "Open"                  # Açık
        IN_PROGRESS = "in_progress", "In Progress"  # İşlemde
        DONE = "done", "Done"                  # Tamamlandı
        CANCELLED = "cancelled", "Cancelled"    # İptal

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.PROTECT,
        related_name="service_requests",
    )
    request_type = models.CharField(max_length=20, choices=RequestType.choices)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.NORMAL)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)

    # Talep açıldığında maliyet çoğu zaman henüz bilinmez; iş ilerledikçe
    # (assigned_to atandıkça, iş yapıldıkça) elle güncellenir.
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_service_requests",
    )

    class Meta:
        db_table = "service_requests"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.vehicle.plate} — {self.request_type} ({self.status})"
