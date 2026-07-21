"""Filters for GET /api/vehicles — see PDF VEH-2 (segment/vites/fiyat filtreleri)."""

import django_filters

from .models import Vehicle


class VehicleFilter(django_filters.FilterSet):
    # daily_price bir ARALIK (min/max) olarak filtrelenmek istendiği için
    # (örn. "1000 TL altı"), django-filter'ın hazır RangeFilter'ını
    # kullanıyoruz — bu tek satır, ?daily_price_min= ve ?daily_price_max=
    # sorgu parametrelerini otomatik olarak destekler (gte/lte mantığını
    # kendi içinde barındırır, elle iki ayrı filtre yazmamıza gerek kalmaz).
    daily_price = django_filters.RangeFilter()

    class Meta:
        model = Vehicle
        # Bunlar basit "tam eşitlik" filtreleri: ?segment=suv gelirse
        # sadece segment'i tam "suv" olan araçlar döner.
        fields = ["segment", "transmission", "fuel", "status", "location"]
