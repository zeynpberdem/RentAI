"""Serializer for handovers — see PDF HND-1/HND-2."""

import json
import re

from django.utils import timezone
from rest_framework import serializers

from reservations.helpers import Status as ReservationStatus
from service_requests.helpers import Priority as RequestPriority
from service_requests.helpers import RequestType
from service_requests.models import ServiceRequest
from vehicles.helpers import Status as VehicleStatus

from .helpers import Type
from .models import Handover

# Yakıt eksiği başına (yüzde puanı) ücret. Basit, sabit bir oran — PDF
# tam bir formül vermiyor, gerçek kiralama sitelerindeki yaygın pratiğe
# (eksik yakıt + servis ücreti) uygun, en basit hâliyle uyguladık.
FUEL_SHORTAGE_RATE_PER_PERCENT = 20

# Müşteriden alınan hasar/yakıt ücreti ile Bakım Merkezi'ndeki gerçek
# onarım/servis maliyeti (ServiceRequest.cost) artık AYNI değil — öncekinde
# ikisi birebir aynı tahminden geliyordu, yani şirket hasar/yakıt tarafında
# ne kâr ne zarar ediyordu (tam denk). Operatörün isteğiyle müşteriden
# alınan tarafa bu marj uygulanıyor, Bakım Merkezi'ndeki maliyet ise hep
# gerçek (marjsız) tahminde kalıyor — aradaki fark şirketin kârı.
DAMAGE_MARKUP_RATE = 1.25

# Yıkama için hasar/yakıt gibi bir "ne kadar kirli" ölçeği yok — kirli/temiz
# ikili bir işaret (bkz. Handover.is_dirty), bu yüzden sabit bir yıkama
# ücreti yeterli. Müşteriden ekstra tahsil edilmiyor (bkz. HandoverSerializer.
# create) — sadece Bakım Merkezi'ndeki gerçek maliyeti (gider) temsil eder.
WASH_COST = 150

# damage_notes serbest metin bir alan ama frontend (bkz. FleetReservationsView.vue
# formatDamageNotes) hangi parçaların hasarlı işaretlendiğini "...||JSON:{...}||"
# şeklinde aynı metnin sonuna gömüyor — hasar var mı yok mu diye buradan
# bakıyoruz. JSON bloğu yoksa (eski/manuel girilmiş kayıtlar) düz metne bakıp
# "Hasar Yok" dışında bir şey yazılmışsa hasar var sayıyoruz.
DAMAGE_JSON_PATTERN = re.compile(r"\|\|JSON:(.*?)\|\|")


def _has_reported_damage(damage_notes):
    if not damage_notes:
        return False
    match = DAMAGE_JSON_PATTERN.search(damage_notes)
    if match:
        try:
            damages = json.loads(match.group(1))
            return any(damages.values())
        except (ValueError, AttributeError):
            pass  # bozuk JSON — aşağıdaki düz metin kontrolüne düş
    human_text = damage_notes.split("||")[0].strip()
    return human_text not in ("", "Hasar Yok")


# Çökme/kırık ve eksik parça, aracı fiilen yola çıkaramayacak kadar ciddi —
# bunlar tek başına aracı otomatik "Bakımda"ya düşürür. Çizik/sürtme/leke
# gibi kozmetik hasarlar TEK BAŞINA artık aracı yoldan çekmiyor (Hacer
# Hanım'ın isteği: küçük bir çizik için araç sanayiye gitmek zorunda değil)
# — talep yine otomatik açılır (kayıt için), ama araç Müsait kalır, operatör
# isterse Araçlar ekranından elle "Bakıma Al" der (bkz. VehicleWriteSerializer,
# FleetVehiclesView.vue toggleMaintenance).
SEVERE_DAMAGE_TYPES = {"crash", "missing"}


def _has_severe_damage(damage_notes):
    if not damage_notes:
        return False
    match = DAMAGE_JSON_PATTERN.search(damage_notes)
    if not match:
        return False
    try:
        damages = json.loads(match.group(1))
    except (ValueError, AttributeError):
        return False
    return any(damage_type in SEVERE_DAMAGE_TYPES for damage_type in damages.values())


# Hasar tipi başına kabaca bir onarım maliyeti — PDF bir formül vermiyor,
# FUEL_SHORTAGE_RATE_PER_PERCENT'teki gibi pragmatik/basit sabitler
# (Bakım Merkezi'nde otomatik açılan talebin cost alanına yazılır;
# operatör isterse sonradan elle düzeltir). Etiketler için bkz.
# FleetReservationsView.vue DAMAGE_LABELS.
DAMAGE_REPAIR_COST = {
    "scratch": 500,  # Çizik
    "rubbing": 300,  # Sürtme
    "stain": 400,  # Leke / Boyalı
    "crash": 3000,  # Çökme / Kırık
    "missing": 1500,  # Eksik
}

# Bakım Merkezi'ndeki Hasar kutusunda ve Rezervasyon Geçmişi'ndeki fiyat
# dökümünde parça parça göstermek için — frontend'deki hasar haritasıyla
# (FleetReservationsView.vue PART_LABELS/DAMAGE_LABELS) birebir aynı
# tutulmalı, aksi halde iki taraf farklı isim gösterir.
PART_LABELS = {
    "hood": "Kaput",
    "left_front_fender": "Sol Ön Çamurluk",
    "left_front_door": "Sol Ön Kapı",
    "left_rear_door": "Sol Arka Kapı",
    "left_rear_fender": "Sol Arka Çamurluk",
    "rear_bumper": "Arka Tampon",
    "front_bumper": "Ön Tampon",
    "trunk": "Bagaj Kapağı",
    "roof": "Tavan",
    "right_rear_fender": "Sağ Arka Çamurluk",
    "right_rear_door": "Sağ Arka Kapı",
    "right_front_door": "Sağ Ön Kapı",
    "right_front_fender": "Sağ Ön Çamurluk",
}

DAMAGE_TYPE_LABELS = {
    "scratch": "Çizik",
    "rubbing": "Sürtme",
    "stain": "Leke / Boyalı",
    "crash": "Çökme / Kırık",
    "missing": "Eksik",
}


def _damage_line_items(damage_notes, markup=1):
    """Her hasarlı parçayı kendi onarım maliyetiyle ayrı bir satır olarak
    döner, ör. [{"label": "Tavan (Çizik)", "cost": 500}, ...].

    markup=1 (varsayılan): Bakım Merkezi'nde gösterilen GERÇEK maliyet
    (ServiceRequest.cost ile aynı). markup=DAMAGE_MARKUP_RATE verilirse
    müşteriden alınan (Rezervasyon Geçmişi'ndeki) tutarı döner — ikisi artık
    kasıtlı olarak farklı (bkz. DAMAGE_MARKUP_RATE)."""
    if not damage_notes:
        return []
    match = DAMAGE_JSON_PATTERN.search(damage_notes)
    if not match:
        return []
    try:
        damages = json.loads(match.group(1))
    except ValueError:
        return []
    items = []
    for part_key, damage_type in damages.items():
        if not damage_type:
            continue
        part_label = PART_LABELS.get(part_key, part_key)
        type_label = DAMAGE_TYPE_LABELS.get(damage_type, damage_type)
        items.append({
            "label": f"{part_label} ({type_label})",
            "cost": round(DAMAGE_REPAIR_COST.get(damage_type, 0) * markup),
        })
    return items


def _estimate_damage_cost(damage_notes, markup=1):
    return sum(item["cost"] for item in _damage_line_items(damage_notes, markup=markup))


def _fuel_shortage_charge(fuel_shortage_percent, markup=1):
    if fuel_shortage_percent <= 0:
        return 0
    return round(fuel_shortage_percent * FUEL_SHORTAGE_RATE_PER_PERCENT * markup)


class HandoverListSerializer(serializers.ModelSerializer):
    """GET /api/handovers — Teslimat Listesi ekranı. Yazma serializer'ının
    (HandoverSerializer) aksine, aracı/müşteriyi okunabilir şekilde
    (plaka, marka/model, ad) gösterir; reservation'ı ayrıca id olarak
    tekrar göstermeye gerek yok, zaten vehicle/customer bilgisi yeterli."""

    vehicle_plate = serializers.CharField(source="reservation.vehicle.plate", read_only=True)
    vehicle_label = serializers.SerializerMethodField()
    customer_name = serializers.SerializerMethodField()

    class Meta:
        model = Handover
        fields = [
            "id",
            "type",
            "vehicle_plate",
            "vehicle_label",
            "customer_name",
            "odometer_km",
            "fuel_level",
            "damage_notes",
            "extra_charge",
            "created_at",
        ]

    def get_vehicle_label(self, handover):
        vehicle = handover.reservation.vehicle
        return f"{vehicle.brand} {vehicle.model}"

    def get_customer_name(self, handover):
        customer = handover.reservation.customer
        full_name = f"{customer.first_name} {customer.last_name}".strip()
        return full_name or customer.email


class HandoverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Handover
        fields = [
            "id",
            "reservation",
            "type",
            "odometer_km",
            "fuel_level",
            "damage_notes",
            "is_dirty",
            "extra_charge",
        ]
        # extra_charge müşteri/operatör tarafından gönderilmez, biz hesaplarız.
        read_only_fields = ["extra_charge"]

    def validate(self, attrs):
        reservation = attrs["reservation"]
        handover_type = attrs["type"]

        if handover_type == Type.DELIVERY:
            if reservation.status not in (
                ReservationStatus.PENDING,
                ReservationStatus.CONFIRMED,
            ):
                raise serializers.ValidationError(
                    "Bu rezervasyon teslim edilebilir bir durumda değil."
                )
            if Handover.objects.filter(
                reservation=reservation, type=Type.DELIVERY
            ).exists():
                raise serializers.ValidationError(
                    "Bu rezervasyon için zaten bir teslim kaydı var."
                )

        else:  # RETURN
            if reservation.status != ReservationStatus.ACTIVE:
                raise serializers.ValidationError(
                    "Bu rezervasyon iade edilebilir (active) bir durumda değil — "
                    "önce teslim edilmiş olmalı."
                )
            if Handover.objects.filter(
                reservation=reservation, type=Type.RETURN
            ).exists():
                raise serializers.ValidationError(
                    "Bu rezervasyon için zaten bir iade kaydı var."
                )

        return attrs

    def create(self, validated_data):
        reservation = validated_data["reservation"]

        if validated_data["type"] == Type.DELIVERY:
            reservation.status = ReservationStatus.ACTIVE
            reservation.save()

            # Araç fiziksel olarak müşteriye teslim edildi — "kirada" artık
            # buradan otomatik set ediliyor (bkz. VehicleWriteSerializer.validate,
            # elle "kirada" seçilememesinin sebebi de bu: tek doğru kaynak burası).
            vehicle = reservation.vehicle
            vehicle.status = VehicleStatus.RENTED
            # Teslim anında girilen kilometre aracın güncel km'si olur — daha
            # önce hiç yazılmıyordu, Bakım Merkezi'nde her zaman 0 görünüyordu.
            vehicle.current_km = validated_data["odometer_km"]
            vehicle.save()

        else:  # RETURN
            # Teslim kaydındaki yakıt seviyesiyle kıyaslıyoruz — eksikse
            # ek ücret hesaplanır, fazlaysa/aynıysa ücret alınmaz.
            delivery = Handover.objects.get(
                reservation=reservation, type=Type.DELIVERY
            )
            fuel_shortage_percent = max(delivery.fuel_level - validated_data["fuel_level"], 0)
            damage_notes = validated_data.get("damage_notes", "")

            # Müşteriden alınan (gelir) ile Bakım Merkezi'ndeki gerçek maliyet
            # (gider, ServiceRequest.cost) artık kasıtlı olarak farklı — bkz.
            # DAMAGE_MARKUP_RATE. fuel_repair_cost/damage_repair_cost gerçek
            # (marjsız) tahmin, aşağıda ServiceRequest.cost'a bunlar yazılır.
            fuel_repair_cost = _fuel_shortage_charge(fuel_shortage_percent)
            fuel_customer_charge = _fuel_shortage_charge(fuel_shortage_percent, markup=DAMAGE_MARKUP_RATE)
            damage_repair_cost = _estimate_damage_cost(damage_notes)
            damage_customer_charge = _estimate_damage_cost(damage_notes, markup=DAMAGE_MARKUP_RATE)

            total_extra_charge = fuel_customer_charge + damage_customer_charge
            if total_extra_charge > 0:
                validated_data["extra_charge"] = total_extra_charge

            # Geç/erken iade ücreti: planlanan end_date ile iadenin yapıldığı
            # gün karşılaştırılır. Her başlayan geç gün için 1 tam günlük
            # daily_price ceza, her erken kalan gün için 1 tam günlük
            # daily_price indirim (Hacer Hanım'ın kuralı: gün bazlı, saatlik
            # kısmi hesap yok). Bu RETURN kaydı bir rezervasyon için sadece
            # bir kez oluşturulabildiği için (bkz. validate() yukarıda) bu
            # hesap tekrar tekrar çalışıp üst üste binmez.
            # .date() değil timezone.localtime(...).date(): start_date/end_date
            # veritabanında UTC olarak tutuluyor, çıplak .date() UTC takvim
            # gününü verir — İstanbul yerel gününe çevirmeden kullanırsak
            # gece yarısına yakın rezervasyonlarda 1 gün kayabilir (bkz.
            # TIME_ZONE = Europe/Istanbul, settings.py).
            today = timezone.localtime(timezone.now()).date()
            scheduled_end = timezone.localtime(reservation.end_date).date()
            daily_price = reservation.vehicle.daily_price

            if today > scheduled_end:
                late_days = (today - scheduled_end).days
                reservation.late_fee_amount = late_days * daily_price
            elif today < scheduled_end:
                early_days = (scheduled_end - today).days
                # min(..., total_price - daily_price): indirim, aracın teslim/iade
                # edildiği günün ücretini asla götürmesin — o gün için zaten
                # anlaşma yapılıp araç fiilen kullanıldı, en az 1 günlük ücret
                # her zaman kalmalı (önceden tek günlük, planlanandan önce
                # teslim edilip aynı gün iade edilen kiralamalarda tutar 0'a
                # düşüyordu, sanki hiç kiralanmamış gibi görünüyordu).
                reservation.early_return_discount = min(
                    early_days * daily_price, max(reservation.total_price - daily_price, 0)
                )

            reservation.total_price = (
                reservation.total_price
                + reservation.late_fee_amount
                - reservation.early_return_discount
                + total_extra_charge
            )

            reservation.status = ReservationStatus.COMPLETED
            reservation.save()

            # Handover kaydını burada (fonksiyon sonunda değil) oluşturuyoruz —
            # aşağıda açılan ServiceRequest'in hangi iadeden doğduğunu
            # işaretleyebilmek için (bkz. ServiceRequest.handover) elimizde
            # gerçek bir Handover instance'ı olması lazım.
            handover = super().create(validated_data)

            # Araç fiziksel olarak geri alındı. Hasar varsa Bakım Merkezi'nde
            # bir talep otomatik açılıyor (ciddiyse HIGH, kozmetikse NORMAL
            # öncelik), sadece yakıt eksikse NORMAL öncelikli bir servis
            # talebi, sadece kirliyse LOW öncelikli bir yıkama talebi —
            # operatör ayrıca elle girmek zorunda kalmaz. Aynı ziyarette
            # birden fazlası varsa TEK talep açılıyor, öncelik sırası
            # hasar > yakıt > kirlilik (en ciddisi hangi tür/öncelikte
            # açılacağını belirler, maliyetler toplanır).
            vehicle = reservation.vehicle
            # İadede girilen kilometre de aynı şekilde güncel km'yi günceller.
            vehicle.current_km = validated_data["odometer_km"]
            has_damage = _has_reported_damage(damage_notes)
            has_severe_damage = _has_severe_damage(damage_notes)
            needs_refuel = validated_data["fuel_level"] < 100
            is_dirty = validated_data.get("is_dirty", False)

            if has_damage or needs_refuel or is_dirty:
                combined_cost = (
                    (damage_repair_cost if has_damage else 0)
                    + (fuel_repair_cost if needs_refuel else 0)
                    + (WASH_COST if is_dirty else 0)
                )
                if has_severe_damage:
                    request_type, priority = RequestType.MAINTENANCE, RequestPriority.HIGH
                elif has_damage:
                    request_type, priority = RequestType.MAINTENANCE, RequestPriority.NORMAL
                elif needs_refuel:
                    request_type, priority = RequestType.SERVICE, RequestPriority.NORMAL
                else:
                    request_type, priority = RequestType.WASH, RequestPriority.LOW
                # cost=combined_cost: marjsız, gerçek maliyet toplamı (müşteriden
                # alınan damage/fuel_customer_charge'dan bilerek farklı, bkz.
                # DAMAGE_MARKUP_RATE) — Bakım Merkezi'nin gerçek gideri budur.
                ServiceRequest.objects.create(
                    vehicle=vehicle,
                    handover=handover,
                    request_type=request_type,
                    priority=priority,
                    cost=combined_cost,
                )

            # Yakıt dolumu/yıkama fiziksel olarak beklendiği ya da ciddi bir
            # hasar (çökme/eksik parça) olduğu sürece araç tekrar kiralanabilir
            # listesine düşmüyor. Kozmetik hasar (çizik/sürtme/leke) TEK
            # BAŞINA artık aracı otomatik bakıma düşürmüyor — talep yukarıda
            # yine açıldı (kayıt için), araç Müsait kalıyor, operatör isterse
            # Araçlar ekranından elle "Bakıma Al" der.
            if has_severe_damage or needs_refuel or is_dirty:
                vehicle.status = VehicleStatus.MAINTENANCE
            else:
                vehicle.status = VehicleStatus.AVAILABLE
            vehicle.save()

            return handover

        return super().create(validated_data)