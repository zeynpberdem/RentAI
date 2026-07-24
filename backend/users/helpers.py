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
