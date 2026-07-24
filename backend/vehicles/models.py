"""
Vehicle inventory models — see PDF section 3.2 (Vehicle).

Location is intentionally minimal for now (just enough for the Vehicle
FK to point somewhere real). It will likely grow (address, phone) once
the Handover / operator-panel work starts in Week 3.
"""
# PDF'in 3.2 (Vehicle) bölümüne karşılık gelen araç envanteri modelleri.
# Location şimdilik bilerek minimal tutuldu — sadece Vehicle'ın FK ile
# bağlanabileceği gerçek bir şube kaydı olsun diye var. 3. haftada
# teslim/iade (Handover) ve operatör paneli işine başlanınca muhtemelen
# adres/telefon gibi alanlarla büyüyecek — o zaman ekleriz, şimdiden
# tahminle (speculative) alan eklemiyoruz.

from django.db import models

from core.models import BaseModel

from .helpers import Fuel, Segment, Status, Transmission


class Location(BaseModel):
    """A branch / office where vehicles are based and returned."""

    name = models.CharField(max_length=100)   # Şube adı, örn. "Kadıköy Şubesi"
    city = models.CharField(max_length=100)   # Şehir, filtreleme/arama için ayrı tutuluyor

    class Meta:
        db_table = "locations"
        ordering = ["city", "name"]

    def __str__(self):
        return f"{self.name} ({self.city})"


class Vehicle(BaseModel):
    """A single rentable car in the fleet."""

    brand = models.CharField(max_length=50)    # Marka, örn. "Toyota"
    model = models.CharField(max_length=50)    # Model, örn. "Corolla"
    segment = models.CharField(max_length=20, choices=Segment.choices)
    transmission = models.CharField(max_length=20, choices=Transmission.choices)
    fuel = models.CharField(max_length=20, choices=Fuel.choices)
    seats = models.PositiveSmallIntegerField()  # Koltuk sayısı, negatif olamaz

    # unique=True -> bu gerçek bir DB kısıtıdır (PostgreSQL UNIQUE INDEX
    # oluşturur), yukarıdaki choices alanlarından farklı olarak veritabanı
    # seviyesinde de aynı plakayı iki kez engeller.
    plate = models.CharField(max_length=20, unique=True)

    daily_price = models.DecimalField(max_digits=10, decimal_places=2)
    # Decimal kullandık, float DEĞİL — para/fiyat hesaplarında float
    # yuvarlama hatası yapar (örn. 0.1 + 0.2 != 0.3), Decimal tam kesinlik verir.

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE,
    )

    # on_delete=PROTECT -> üzerinde hâlâ araç kayıtlı bir Location
    # yanlışlıkla silinemez; önce o Location'daki araçlar başka şubeye
    # taşınmalı ya da silinmeli. Veri bütünlüğünü korumak için bilinçli
    # bir tercih (CASCADE olsaydı, şube silinince araçlar da silinirdi).
    location = models.ForeignKey(
        Location,
        on_delete=models.PROTECT,
        related_name="vehicles",
    )

    # blank/null=True: her aracın görseli olmak zorunda değil, sonradan
    # da eklenebilir. upload_to="vehicles/": dosyalar MEDIA_ROOT altında
    # "vehicles/" klasörüne kaydedilir (bkz. config/settings.py).
    image = models.ImageField(upload_to="vehicles/", blank=True, null=True)

    has_ac = models.BooleanField(default=False)     # Klima
    is_4wd = models.BooleanField(default=False)     # Dörtçeker

    class Meta:
        db_table = "vehicles"
        ordering = ["-created_at"]
        # Gerçek bir veritabanı kısıtı (unique=True'daki gibi) — elektrikli
        # araçların manuel vitesi olmaz (tek hızlı dişli sistemleri var).
        # Bu satır sayesinde API'yi, admin panelini, hatta ham SQL'i bile
        # atlayarak biri bu kombinasyonu eklemeye çalışsa PostgreSQL'in
        # kendisi reddeder — sadece bizim yazdığımız koda bağlı değil.
        constraints = [
            models.CheckConstraint(
                # Fuel/Transmission artık helpers.py'dan import edilen, dosya
                # seviyesinde tanımlı sınıflar olduğu için (eskiden olduğu gibi
                # Vehicle'ın içine gömülü DEĞİL) burada doğrudan isimleriyle
                # kullanılabiliyorlar — ham metin yazmaya gerek kalmadı.
                condition=~(models.Q(fuel=Fuel.ELECTRIC) & models.Q(transmission=Transmission.MANUAL)),
                name="electric_vehicles_cannot_have_manual_transmission",
            ),
        ]

    def __str__(self):
        return f"{self.brand} {self.model} ({self.plate})"