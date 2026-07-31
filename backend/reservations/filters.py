"""Filters for GET /api/reservations — arama + tarih araliği + durum."""

import django_filters
from django.db.models import Q

from .models import Reservation


class ReservationFilter(django_filters.FilterSet):
    # Müşteri adı/soyadı/e-postası ya da araç plakasından herhangi birine
    # uyan rezervasyonları döner — frontend'de arama backend'e gidiyor.
    search = django_filters.CharFilter(method="filter_search")

    # "Tarih ile filtreleyin" — başlangıç tarihi bu aralıkta olan rezervasyonlar.
    start_date_from = django_filters.DateFilter(field_name="start_date", lookup_expr="gte")
    start_date_to = django_filters.DateFilter(field_name="start_date", lookup_expr="lte")

    class Meta:
        model = Reservation
        fields = ["status", "type", "source"]

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(vehicle__plate__icontains=value)
            | Q(customer__first_name__icontains=value)
            | Q(customer__last_name__icontains=value)
            | Q(customer__email__icontains=value)
        )
