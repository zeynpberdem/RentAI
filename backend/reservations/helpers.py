"""Model'in içine gömülmeyen yardımcı sabitler (TextChoices) — bkz. PDF 3.3 (Reservation).

Bu, veritabanında bu haliyle durmuyor, sadece Reservation.status alanına
yazılabilecek metinleri sınırlıyor. Model dosyasının dışında tutuluyor ki
başka dosyalar (filters, views, testler) Reservation sınıfını import etmeden
bu sabite ulaşabilsin.
"""

from django.db import models

from vehicles.helpers import Segment

# Segment başına minimum sürücü yaşı — rezervasyon oluşturulurken otomatik
# kontrol edilir (bkz. ReservationCreateSerializer.validate). Referans
# projedeki gibi bu kontrol OTOMATİK — ayrı bir "operatör onaylıyor" ekranı
# yok, geçerse rezervasyon direkt Teslim Bekliyor (CONFIRMED) durumunda açılır.
MIN_DRIVER_AGE_BY_SEGMENT = {
    Segment.ECONOMY: 21,
    Segment.MID: 21,
    Segment.SUV: 25,
    Segment.LUXURY: 30,
}

# Segment başına minimum ehliyet deneyimi (yıl) — sürücünün license_issue_date
# alanından hesaplanır, yeni bir alan gerekmiyor (bkz. ReservationCreateSerializer.validate).
MIN_LICENSE_EXPERIENCE_YEARS_BY_SEGMENT = {
    Segment.ECONOMY: 1,
    Segment.MID: 1,
    Segment.SUV: 2,
    Segment.LUXURY: 3,
}

# Segment başına minimum Findeks skoru (0-1900) — sürücünün findeks_score
# alanı BOŞSA bu kontrol atlanır (henüz not girilmemiş demektir, kiralamayı
# engellemiyoruz). Economy/Mid'de eşik yok, üst segmentlerde risk arttıkça
# devreye giriyor (bkz. users.models.User.findeks_score).
MIN_FINDEKS_SCORE_BY_SEGMENT = {
    Segment.SUV: 1500,
    Segment.LUXURY: 1700,
}


class Status(models.IntegerChoices):
    """ bkz. Rezervasyon Geçmişi
    tartışması. Akış: PENDING -> CONFIRMED -> ACTIVE -> COMPLETED (bu üçü
    sırayla ilerler); CANCELLED bilerek 99 (sıralı akışın DIŞINDA bir uç/
    özel kod) — sadece PENDING ya da CONFIRMED durumundayken mümkün, ACTIVE
    (araç kirada) olduktan sonra ARTIK iptal edilemez (bkz. views.cancel)."""

    PENDING = 1, "Onay Bekliyor"
    CONFIRMED = 2, "Teslim Bekliyor"
    ACTIVE = 3, "Kirada"
    COMPLETED = 4, "Tamamlandı"
    CANCELLED = 99, "İptal Edildi"


class ReservationType(models.TextChoices):
    """Bkz. Ziraat Filo referansındaki "Rezervasyon Tipi" sütunu."""

    SHORT_TERM = "short_term", "Kısa Dönem"
    LONG_TERM = "long_term", "Uzun Dönem"
    CORPORATE = "corporate", "Kurumsal"


class ReservationSource(models.TextChoices):
    """Bkz. Ziraat Filo referansındaki "Rezervasyon Kaynağı" sütunu —
    rezervasyonun hangi kanaldan geldiği (şube, çağrı merkezi, vb.)."""

    BRANCH = "branch", "Şube"
    CALL_CENTER = "call_center", "Çağrı Merkezi"
    WEB = "web", "Web Sitesi"
    AGENCY = "agency", "Online Acenta"
