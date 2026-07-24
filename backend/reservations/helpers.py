"""Model'in içine gömülmeyen yardımcı sabitler (TextChoices) — bkz. PDF 3.3 (Reservation).

Bu, veritabanında bu haliyle durmuyor, sadece Reservation.status alanına
yazılabilecek metinleri sınırlıyor. Model dosyasının dışında tutuluyor ki
başka dosyalar (filters, views, testler) Reservation sınıfını import etmeden
bu sabite ulaşabilsin.
"""

from django.db import models


class Status(models.TextChoices):
    PENDING = "pending", "Pending"        # Onay bekliyor
    CONFIRMED = "confirmed", "Confirmed"  # Onaylandı
    ACTIVE = "active", "Active"            # Araç şu an müşteride
    COMPLETED = "completed", "Completed"   # İade edildi, tamamlandı
    CANCELLED = "cancelled", "Cancelled"    # İptal edildi
