"""Model'in içine gömülmeyen yardımcı sabit (TextChoices) — bkz. PDF 3.4 (Handover).

Bu, veritabanında bu haliyle durmuyor, sadece Handover.type alanına
yazılabilecek metinleri sınırlıyor. Model dosyasının dışında tutuluyor ki
başka dosyalar (serializers, testler) Handover sınıfını import etmeden bu
sabite ulaşabilsin.
"""

from django.db import models


class Type(models.TextChoices):
    DELIVERY = "delivery", "Delivery"  # Teslim
    RETURN = "return", "Return"        # İade
