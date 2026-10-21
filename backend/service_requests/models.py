"""ServiceRequest model — see PDF section 3.5 and SRV-1/SRV-2."""

from django.conf import settings
from django.db import models

from core.models import BaseModel
from vehicles.models import Vehicle

from .helpers import Priority, RequestType, Status


class ServiceRequest(BaseModel):
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

    # status DONE'a geçtiğinde set edilir (bkz. ServiceRequestUpdateSerializer.update) —
    # updated_at kullanılamaz çünkü o priority/assigned_to gibi başka bir alan
    # değiştiğinde de güncellenir, sadece gerçek "bakımdan çıkış" tarihini istiyoruz.
    completed_at = models.DateTimeField(null=True, blank=True)

    # Bu talebi otomatik açan iade kaydı (bkz. handovers/serializers.py
    # HandoverSerializer.create) — null olabilir çünkü "Talep Aç" ile elle
    # açılan talepler bir iadeye bağlı değil. Bakım Merkezi'nde "Son
    # Kiralayan/Hasar" bilgisini ARACIN en son iadesine değil, doğrudan BU
    # talebi açan iadeye bakarak doğru göstermek için (araç bu talep
    # kapandıktan sonra başka bir kiralama+iade döngüsünden geçmiş olabilir).
    handover = models.ForeignKey(
        "handovers.Handover",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="service_requests",
    )

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
