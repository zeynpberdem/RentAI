"""Model'lerin içine gömülmeyen yardımcı sabitler (TextChoices) — bkz. PDF 3.2 (Vehicle).

Bunlar veritabanında bu haliyle durmuyor, sadece Vehicle'ın ilgili alanlarına
yazılabilecek metinleri sınırlıyor. Model dosyasının dışında tutuluyor ki hem
models.py sade kalsın hem de başka dosyalar (serializers, filters, testler)
Vehicle sınıfını import etmeden bu sabitlere ulaşabilsin.
"""

from django.db import models


class Segment(models.TextChoices):
    ECONOMY = "economy", "Economy"     # Ekonomi
    MID = "mid", "Mid-size"            # Orta segment
    SUV = "suv", "SUV"
    LUXURY = "luxury", "Luxury"        # Lüks


class Transmission(models.TextChoices):
    MANUAL = "manual", "Manual"            # Manuel vites
    AUTOMATIC = "automatic", "Automatic"    # Otomatik vites


class Fuel(models.TextChoices):
    PETROL = "petrol", "Petrol"        # Benzin
    DIESEL = "diesel", "Diesel"        # Dizel
    ELECTRIC = "electric", "Electric"  # Elektrik
    HYBRID = "hybrid", "Hybrid"        # Hibrit


class Status(models.TextChoices):
    AVAILABLE = "available", "Available"        # Müsait / kiralanabilir
    RENTED = "rented", "Rented"                  # Şu an kirada
    MAINTENANCE = "maintenance", "Maintenance"    # Bakımda / kiralanamaz