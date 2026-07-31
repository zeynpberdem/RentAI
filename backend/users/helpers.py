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
    """Türkiye'deki sürücü belgesi sınıfları — bkz. profil tamamlama akışı."""

    A1 = "A1", "A1"
    A2 = "A2", "A2"
    A = "A", "A"
    B1 = "B1", "B1"
    B = "B", "B"
    BE = "BE", "BE"
    C1 = "C1", "C1"
    C = "C", "C"
    D1 = "D1", "D1"
    D = "D", "D"
