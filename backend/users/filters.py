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
        # "mert özel" gibi ad+soyad birlikte aranınca ("Mert" first_name'de,
        # "Özel" last_name'de ayrı sütunlarda olduğu için) tüm ifadeyi TEK
        # parça olarak her alanda arasak hiçbiri eşleşmez — bu yüzden
        # boşlukla kelimelere bölüp her kelimenin en az bir alanda geçmesini
        # istiyoruz (AND), tıpkı DRF'in SearchFilter'ı gibi.
        #
        # Bunu SQL icontains/ILIKE ile YAPAMIYORUZ: veritabanı "C" (POSIX)
        # locale'iyle kurulu (bkz. `SHOW LC_CTYPE`), yani Postgres'in
        # büyük/küçük harf katlaması sadece ASCII'yi kapsıyor — Ö/ö, Ü/ü,
        # Ş/ş, Ç/ç, Ğ/ğ gibi Türkçe harfleri katlamıyor (ör.
        # `'Özel' ILIKE '%özel%'` -> false). Kalıcı çözüm veritabanını UTF8
        # destekli bir locale ile yeniden kurmak ama bu yıkıcı bir işlem;
        # onun yerine adayları (zaten role=CUSTOMER, is_active=True ile
        # sınırlı — bkz. get_queryset) Python'a çekip Python'ın doğru
        # çalışan str.casefold()'uyla eşleştiriyoruz.
        terms = [term.casefold() for term in value.split()]
        if not terms:
            return queryset

        matched_ids = []
        for driver in queryset:
            haystack = " ".join(
                filter(None, [driver.first_name, driver.last_name, driver.email, driver.phone])
            ).casefold()
            if all(term in haystack for term in terms):
                matched_ids.append(driver.id)
        return queryset.filter(id__in=matched_ids)

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
