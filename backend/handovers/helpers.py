"""Model'in içine gömülmeyen yardımcı sabit (TextChoices) — bkz. PDF 3.4 (Handover).

Bu, veritabanında bu haliyle durmuyor, sadece Handover.type alanına
yazılabilecek metinleri sınırlıyor. Model dosyasının dışında tutuluyor ki
başka dosyalar (serializers, testler) Handover sınıfını import etmeden bu
sabite ulaşabilsin.
"""

from django.db import models


class Type(models.TextChoices):
    # NOT: TextChoices sadece STRING değer kabul eder (dün buraya çıplak
    # sayı (1,2,3,4) yazılmıştı, bu Django'yu açılışta çökertiyordu — bkz.
    # "1 is not a string" hatası). İçerik (geçiş türleri) aynı kaldı, sadece
    # değerler string'e çevrildi.
    CREATE = "create", "Rezervasyon Oluşturuldu"
    WAITING_APPROVE_TO_WAITING_DELIVERY = "waiting_approve_to_waiting_delivery", "Onay bekliyor -> teslim bekliyor"
    WAITING_APPROVE_TO_CANCEL = "waiting_approve_to_cancel", "Onay bekliyor -> iptal"
    WAITING_DELIVERY_TO_RENT = "waiting_delivery_to_rent", "Teslim bekliyor -> kirada"
    DELIVERY = "delivery", "Delivery"  # Teslim
    RETURN = "return", "Return"        # İade
