"""Model'lerin içine gömülmeyen yardımcı sabitler (TextChoices) — bkz. PDF 2.2 (Roller).

Bunlar veritabanında bu haliyle durmuyor, sadece User.role alanına yazılabilecek
metinleri (customer/operator/admin) sınırlıyor. Model dosyasının dışında
tutuluyor ki hem models.py sade kalsın hem de başka dosyalar (serializers,
permissions, testler) model sınıfını import etmeden bu sabitlere ulaşabilsin.
"""

from django.db import models


class Role(models.TextChoices):
    CUSTOMER = "customer", "Customer"    # Müşteri
    OPERATOR = "operator", "Operator"    # Operatör
    ADMIN = "admin", "Admin"             # Yönetici


class LicenseClass(models.TextChoices):
    """Sürücü belgesi sınıfları — bkz. profil tamamlama akışı.

    Sadece B (binek araç) var: filo economy/mid/suv/luxury segmentlerinden
    oluşuyor (bkz. vehicles.helpers.Segment), motosiklet/kamyon/otobüs
    kiralanmıyor — bu yüzden A/A1/A2/BE/C/C1/D/D1 gibi diğer Türkiye
    sınıfları burada anlamsız, kafa karıştırmasın diye listeye alınmadı."""

    B = "B", "B"
