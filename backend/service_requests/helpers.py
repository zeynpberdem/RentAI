"""Model'in içine gömülmeyen yardımcı sabitler (TextChoices) — bkz. PDF 3.5 (ServiceRequest).

Bunlar veritabanında bu haliyle durmuyor, sadece ServiceRequest'in ilgili
alanlarına yazılabilecek metinleri sınırlıyor. Model dosyasının dışında
tutuluyor ki başka dosyalar (serializers, testler) ServiceRequest sınıfını
import etmeden bu sabitlere ulaşabilsin.
"""

from django.db import models


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
