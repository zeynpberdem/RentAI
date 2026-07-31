"""Sürücüler (Drivers) ekranı için arama + profil durumu filtresi."""

import django_filters
from django.db.models import Q

from .models import User


class DriverFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method="filter_search")
    profile_status = django_filters.CharFilter(method="filter_profile_status")

    class Meta:
        model = User
        fields = []

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(first_name__icontains=value)
            | Q(last_name__icontains=value)
            | Q(email__icontains=value)
            | Q(phone__icontains=value)
        )

    def filter_profile_status(self, queryset, name, value):
        # User.is_profile_complete property'siyle aynı kural seti — bir
        # queryset property üzerinden filtrelenemediği için burada Q
        # ifadeleriyle tekrar ediyoruz.
        complete_q = (
            ~Q(first_name="")
            & ~Q(last_name="")
            & ~Q(tc_no="")
            & Q(birth_date__isnull=False)
            & ~Q(license_class="")
            & Q(license_issue_date__isnull=False)
        )
        if value == "complete":
            return queryset.filter(complete_q)
        if value == "incomplete":
            return queryset.exclude(complete_q)
        return queryset
