"""Serializers for reservations — see PDF RES-1/2/3."""

from rest_framework import serializers

from handovers.helpers import Type as HandoverType
from handovers.models import Handover
from vehicles.models import Location
from vehicles.serializers import LocationSerializer, VehicleStaffSerializer

from .helpers import MIN_DRIVER_AGE_BY_SEGMENT, MIN_LICENSE_EXPERIENCE_YEARS_BY_SEGMENT, Status
from .models import Reservation


def _full_years_between(later_date, earlier_date):
    """İki tarih arasındaki TAM (dolmuş) yıl sayısı — yaş ve ehliyet deneyimi
    hesabında ortak kullanılıyor. Örn. 2000-06-15 ile 2026-06-14 arası 25
    tam yıl (henüz 26. yıl dönümüne 1 gün var), 2026-06-15'te 26 olur."""
    return later_date.year - earlier_date.year - (
        (later_date.month, later_date.day) < (earlier_date.month, earlier_date.day)
    )


class ReservationHistoryEventSerializer(serializers.ModelSerializer):
    """Rezervasyon Geçmişi (yaşam döngüsü) penceresinde teslim/iade
    olaylarını göstermek için yalın bir görünüm — sadece tür + zaman."""

    class Meta:
        model = Handover
        fields = ["type", "created_at"]


class ReservationSerializer(serializers.ModelSerializer):
    """Read-only: filo yönetimi listesinde gösterilen tam görünüm.

    Artık sadece operatör görüyor (müşteri kendi hesabıyla giriş yapmıyor)
    — bu yüzden araç tarafında plaka da dahil (VehicleStaffSerializer) ve
    müşteri adı ayrıca ekleniyor; liste ekranında "kim, hangi aracı,
    hangi tarihte kiralamış" tek bakışta görülsün diye.
    """

    vehicle = VehicleStaffSerializer(read_only=True)
    customer_name = serializers.SerializerMethodField()
    pickup_location = LocationSerializer(read_only=True)
    return_location = LocationSerializer(read_only=True)
    is_extended = serializers.SerializerMethodField()
    is_early_return = serializers.SerializerMethodField()
    handovers = ReservationHistoryEventSerializer(many=True, read_only=True)

    class Meta:
        model = Reservation
        fields = [
            "id",
            "customer_name",
            "vehicle",
            "start_date",
            "end_date",
            "status",
            "type",
            "source",
            "pickup_location",
            "return_location",
            "total_price",
            "pricing_snapshot",
            "is_extended",
            "is_early_return",
            "created_at",
            "extended_at",
            "cancelled_at",
            "handovers",
        ]

    def get_customer_name(self, reservation):
        full_name = f"{reservation.customer.first_name} {reservation.customer.last_name}".strip()
        return full_name or reservation.customer.email

    def get_is_extended(self, reservation):
        return reservation.extended_at is not None

    def get_is_early_return(self, reservation):
        # Rezervasyon Listesi'nde tutarın yanına "-" koymak için: gerçek
        # iade (Handover type=return) kaydı, planlanan end_date'ten ÖNCE
        # yapılmışsa erken teslim edilmiş demektir.
        if reservation.status != Status.COMPLETED:
            return False
        return_handover = next(
            (h for h in reservation.handovers.all() if h.type == HandoverType.RETURN), None
        )
        if not return_handover:
            return False
        return return_handover.created_at.date() < reservation.end_date.date()


class ReservationCreateSerializer(serializers.ModelSerializer):
    """Write-only: müşteri sadece araç ve tarih seçer, geri kalanı biz hesaplarız."""

    # required=False: gönderilmezse create()'te aracın kendi şubesine
    # varsayılır (bkz. aşağıdaki create()) — Ziraat Filo'daki gibi farklı
    # bir ofisten teslim/iade seçmek istersen gönderirsin.
    pickup_location = serializers.PrimaryKeyRelatedField(queryset=Location.active_objects.all(), required=False)
    return_location = serializers.PrimaryKeyRelatedField(queryset=Location.active_objects.all(), required=False)

    class Meta:
        model = Reservation
        fields = ["id", "vehicle", "start_date", "end_date", "type", "source", "pickup_location", "return_location"]
        # "customer" bilerek burada YOK: müşteri kendi adına değil de
        # başka birinin adına rezervasyon açamasın diye — customer,
        # view içinde request.user'dan set edilecek (bkz. views.py).
        # "status"/"total_price" de burada YOK: bunlar sistem tarafından
        # hesaplanır, müşteri elle bir fiyat/durum gönderemez.

    def validate(self, attrs):
        # Rezervasyonun kimin adına açıldığı, müşterinin kendi akışında
        # request.user'dır; operatör akışında (bkz. ReservationStaffCreateSerializer)
        # seçilen "customer" alanıdır — hangisi olursa olsun PROFİLİ TAMAMLANMIŞ
        # olması gereken kişi odur.
        customer = attrs.get("customer") or self.context["request"].user
        if not customer.is_profile_complete:
            raise serializers.ValidationError(
                "Rezervasyon yapabilmek için önce profilini tamamlamalısın."
            )

        start = attrs["start_date"]
        end = attrs["end_date"]
        if end <= start:
            raise serializers.ValidationError("end_date, start_date'ten sonra olmalı.")

        # Otomatik uygunluk kontrolü (referans projedeki gibi — ayrı bir
        # "operatör onaylıyor" ekranı YOK): segmente göre minimum sürücü yaşı
        # VE minimum ehliyet deneyimi. İkisi de kiralama BAŞLANGICINDAKİ
        # duruma göre hesaplanır (bugünkü tarihe göre değil), ileri tarihli
        # bir rezervasyon doğru değerlendirilsin diye.
        vehicle = attrs["vehicle"]
        rental_start = start.date()

        min_age = MIN_DRIVER_AGE_BY_SEGMENT.get(vehicle.segment)
        if min_age and customer.birth_date:
            driver_age = _full_years_between(rental_start, customer.birth_date)
            if driver_age < min_age:
                raise serializers.ValidationError(
                    f"{vehicle.get_segment_display()} segmenti için minimum sürücü yaşı {min_age} "
                    f"— sürücünün kiralama başlangıcındaki yaşı {driver_age}."
                )

        min_experience = MIN_LICENSE_EXPERIENCE_YEARS_BY_SEGMENT.get(vehicle.segment)
        if min_experience and customer.license_issue_date:
            experience_years = _full_years_between(rental_start, customer.license_issue_date)
            if experience_years < min_experience:
                raise serializers.ValidationError(
                    f"{vehicle.get_segment_display()} segmenti için minimum ehliyet deneyimi "
                    f"{min_experience} yıl — sürücünün kiralama başlangıcındaki deneyimi {experience_years} yıl."
                )

        # Müsaitlik kontrolü: aynı araç için, tarihleri çakışan ve hâlâ
        # geçerli (iptal/tamamlanmamış) başka bir rezervasyon var mı?
        # Çakışma formülü: mevcut.start < yeni.end VE mevcut.end > yeni.start
        conflicting = Reservation.objects.filter(
            vehicle=attrs["vehicle"],
            start_date__lt=end,
            end_date__gt=start,
        ).exclude(status__in=[Status.CANCELLED, Status.COMPLETED])

        if conflicting.exists():
            raise serializers.ValidationError(
                "Bu araç, seçilen tarih aralığında müsait değil."
            )

        return attrs

    def create(self, validated_data):
        vehicle = validated_data["vehicle"]
        # .date() farkı BİLEREK kullanılıyor (tam datetime farkı değil):
        # start_date/end_date artık saat de taşıyor ama günlük fiyatlandırma
        # hâlâ takvim günü sayısına göre — saat farkı fiyatı etkilemesin.
        # max(...,1): aynı takvim günü içinde farklı saatlerle (ör. 10:00 ->
        # 20:00) yapılan bir rezervasyon date() farkı 0 çıkarıp ücretsiz
        # (total_price=0) olurdu — en az 1 günlük ücret her zaman alınır.
        days = max((validated_data["end_date"].date() - validated_data["start_date"].date()).days, 1)
        total_price = vehicle.daily_price * days

        # Ayrıca belirtilmediyse, teslim/iade aracın kendi şubesi varsayılır.
        validated_data.setdefault("pickup_location", vehicle.location)
        validated_data.setdefault("return_location", vehicle.location)

        validated_data["total_price"] = total_price
        validated_data["pricing_snapshot"] = {
            "daily_price": str(vehicle.daily_price),
            "days": days,
            "total_price": str(total_price),
        }
        # validate()'teki otomatik uygunluk kontrolünü (yaş/segment) zaten
        # geçti — bu yüzden PENDING (Onay Bekliyor) yerine direkt CONFIRMED
        # (Teslim Bekliyor) ile açılıyor; ayrı bir "operatör onaylıyor"
        # ekranı yok (bkz. referans projedeki otomatik akış).
        validated_data["status"] = Status.CONFIRMED
        return super().create(validated_data)


class ReservationExtendSerializer(serializers.Serializer):
    """POST /api/reservations/{id}/extend — sadece yeni bitiş tarihi/saati."""

    end_date = serializers.DateTimeField()


class ReservationStaffCreateSerializer(ReservationCreateSerializer):
    """Write: operatör, filo yönetimi ekranından seçtiği bir sürücü
    (müşteri) adına rezervasyon açar — bkz. PDF'e ek olarak eklenen
    "Sürücüler" ekranı. Aynı doğrulamaları (müsaitlik, profil tamlığı)
    ReservationCreateSerializer'dan miras alır, sadece "customer" alanını
    ekler."""

    class Meta(ReservationCreateSerializer.Meta):
        fields = ReservationCreateSerializer.Meta.fields + ["customer"]

    def validate_customer(self, customer):
        if customer.role != "customer":
            raise serializers.ValidationError("Seçilen kullanıcı müşteri rolünde değil.")
        return customer
