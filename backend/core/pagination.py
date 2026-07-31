"""Projenin ortak sayfalama sınıfı — tüm liste uç noktaları bunu kullanır."""

from rest_framework.pagination import PageNumberPagination


class DefaultPagination(PageNumberPagination):
    """Varsayılan sayfa boyutu (20) settings.py'daki PAGE_SIZE'dan geliyor.

    page_size_query_param: ?page_size=500 gibi bir parametreyle bu varsayılanı
    aşmak isteyen ekranlar için (ör. Rezervasyon Takvimi, Analiz — dropdown/
    toplulaştırma amaçlı "tüm kayıtlar" ihtiyacı). Bu, düz REST_FRAMEWORK
    settings sözlüğüne "PAGE_SIZE_QUERY_PARAM" anahtarı eklemekle YAPILAMIYOR:
    DRF böyle bir global ayarı tanımıyor ve sessizce yok sayıyor — bu yüzden
    ayrı bir Pagination sınıfı tanımlayıp page_size_query_param'ı burada,
    sınıf özelliği olarak set etmemiz gerekiyor.
    """

    page_size_query_param = "page_size"
    max_page_size = 1000
