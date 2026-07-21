"""Filters for GET /api/vehicles — see PDF VEH-2 (segment/vites/fiyat filtreleri)."""

import django_filters

from .models import Vehicle


class VehicleFilter(django_filters.FilterSet):
    # daily_price tek bir değer değil, bir ARALIK (min/max) olarak
    # filtrelenmek istendiği için (örn. "1000 TL altı"), iki ayrı alan
    # tanımlıyoruz: price_min ve price_max. Bunlar Vehicle modelinde
    # doğrudan var olan alanlar değil, django-filter'ın "daily_price'a
    # gte (>=) / lte (<=) uygula" demesini sağlayan özel tanımlar.
    price_min = django_filters.NumberFilter(field_name="daily_price", lookup_expr="gte")
    price_max = django_filters.NumberFilter(field_name="daily_price", lookup_expr="lte")

    class Meta:
        model = Vehicle
        # Bunlar basit "tam eşitlik" filtreleri: ?segment=suv gelirse
        # sadece segment'i tam "suv" olan araçlar döner.
        fields = ["segment", "transmission", "fuel", "status", "location"]
