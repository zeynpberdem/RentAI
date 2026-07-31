"""Filters for GET /api/vehicles — see PDF VEH-2 (segment/vites/fiyat/tarih filtreleri)."""

import django_filters
from django.db.models import Q

from reservations.helpers import Status as ReservationStatus

from .helpers import Fuel, Transmission
from .models import Vehicle


class VehicleFilter(django_filters.FilterSet):
    # Tek bir arama kutusu; plaka/marka/model'den herhangi birine uyan
    # araçları döner — frontend'de arama backend'e gidiyor (client-side
    # değil), bu yüzden büyük filo/sayfalama ile de doğru çalışır.
    search = django_filters.CharFilter(method="filter_search")

    # daily_price bir ARALIK (min/max) olarak filtrelenmek istendiği için
    # (örn. "1000 TL altı"), django-filter'ın hazır RangeFilter'ını
    # kullanıyoruz — bu tek satır, ?daily_price_min= ve ?daily_price_max=
    # sorgu parametrelerini otomatik olarak destekler (gte/lte mantığını
    # kendi içinde barındırır, elle iki ayrı filtre yazmamıza gerek kalmaz).
    daily_price = django_filters.RangeFilter()

    # "en az N koltuk" — tam eşitlik değil, çünkü müşteri "tam 5 koltuklu"
    # değil "en az 5 koltuklu" arar.
    seats_min = django_filters.NumberFilter(field_name="seats", lookup_expr="gte")

    # PDF'in VEH-2 kriteri "tarih filtresi" de istiyor — bu ikisi ayrı
    # sorgu parametreleri (start_date, end_date) ama aynı metodu çalıştırıp
    # "bu tarih aralığında dolu olan araçları listeden çıkar" diyorlar.
    start_date = django_filters.DateFilter(method="filter_availability")
    end_date = django_filters.DateFilter(method="filter_availability")

    # MultipleChoiceFilter: checkbox'larla "otomatik VEYA manuel" gibi
    # birden fazla değer seçilebilsin diye — Meta.fields'taki varsayılan
    # filtre sadece TEK bir değeri kabul ederdi (tam eşitlik).
    transmission = django_filters.MultipleChoiceFilter(choices=Transmission.choices)
    fuel = django_filters.MultipleChoiceFilter(choices=Fuel.choices)

    class Meta:
        model = Vehicle
        # Bunlar basit "tam eşitlik" filtreleri: ?segment=suv gelirse
        # sadece segment'i tam "suv" olan araçlar döner. has_ac/is_4wd
        # BooleanField olduğu için django-filter otomatik olarak
        # ?has_ac=true / ?is_4wd=true şeklinde çalışan bir filtre üretiyor.
        fields = ["segment", "status", "location", "has_ac", "is_4wd"]

    def filter_availability(self, queryset, name, value):
        # start_date VE end_date'in İKİSİ birden gelmeden bir "aralık"tan
        # bahsedilemez — sadece biri gelmişse bu filtreyi uygulamıyoruz.
        start = self.data.get("start_date")
        end = self.data.get("end_date")
        if not (start and end):
            return queryset

        # Fonksiyonun içinde import ediyoruz (dosyanın en üstünde değil):
        # reservations app'i, vehicles app'inin modelini zaten import
        # ediyor (Reservation.vehicle FK'si için) — dosyanın tepesinde
        # tersini yapsaydık döngüsel import (circular import) oluşurdu.
        from reservations.models import Reservation

        # Reservation'da kullandığımız aynı çakışma formülü: mevcut
        # rezervasyonun aralığı, aranan aralıkla kesişiyor mu?
        conflicting_vehicle_ids = Reservation.objects.filter(
            start_date__lt=end,
            end_date__gt=start,
        ).exclude(
            status__in=[ReservationStatus.CANCELLED, ReservationStatus.COMPLETED]
        ).values_list("vehicle_id", flat=True)

        return queryset.exclude(id__in=conflicting_vehicle_ids)

    def filter_search(self, queryset, name, value):
        return queryset.filter(Q(plate__icontains=value) | Q(brand__icontains=value) | Q(model__icontains=value))