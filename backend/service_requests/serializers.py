"""Serializers for service requests — see PDF SRV-1/SRV-2."""

from django.utils import timezone
from rest_framework import serializers

from handovers.helpers import Type as HandoverType
from handovers.models import Handover
from handovers.serializers import _damage_line_items, _fuel_shortage_charge
from vehicles.helpers import Status as VehicleStatus
from vehicles.serializers import VehicleStaffSerializer

from .helpers import Status
from .models import ServiceRequest


def _damage_summary(damage_notes):
    """damage_notes'un insan-okunabilir kısmı — bkz. handovers/serializers.py
    _has_reported_damage'daki aynı ||JSON:...|| ayıklama/"Hasar Yok" mantığı."""
    if not damage_notes:
        return ""
    human_text = damage_notes.split("||")[0].strip()
    return "" if human_text == "Hasar Yok" else human_text

# Bir durumdan hangi durumlara geçilebileceğinin haritası. Boş küme = son
# durum, buradan başka hiçbir yere geçilemez.
ALLOWED_STATUS_TRANSITIONS = {
    Status.OPEN: {Status.IN_PROGRESS, Status.CANCELLED},
    Status.IN_PROGRESS: {Status.DONE, Status.CANCELLED},
    Status.DONE: set(),
    Status.CANCELLED: set(),
}


class ServiceRequestSerializer(serializers.ModelSerializer):
    """Read-only: liste/detay görünümü, araç bilgisi tam gösterilir."""

    # Bu endpoint sadece operatörlere açık (bkz. views.py IsOperator) —
    # bu yüzden plaka da gösterilebilir (public VehicleSerializer'da bilerek yok).
    vehicle = VehicleStaffSerializer(read_only=True)
    last_return_info = serializers.SerializerMethodField()

    class Meta:
        model = ServiceRequest
        fields = [
            "id",
            "vehicle",
            "request_type",
            "priority",
            "status",
            "cost",
            "assigned_to",
            "created_at",
            "completed_at",
            "last_return_info",
        ]

    def get_last_return_info(self, service_request):
        # Öncelik: bu talebi doğrudan açan iade kaydı (bkz. HandoverSerializer.
        # create, ServiceRequest.handover). Bu olmadan (elle "Talep Aç" ile
        # açılmış eski/manuel talepler) aracın en son iadesine düşüyoruz —
        # ama araç bu talep kapandıktan sonra BAŞKA bir kiralama+iade
        # döngüsünden geçmiş olabileceği için (bkz. handover FK'sinin neden
        # eklendiği), "en son iade" artık sadece bu geriye dönük durum için.
        handover = service_request.handover
        if not handover:
            handover = (
                Handover.objects.filter(
                    reservation__vehicle=service_request.vehicle, type=HandoverType.RETURN
                )
                .select_related("reservation__customer")
                .order_by("-created_at")
                .first()
            )
        if not handover:
            return None

        customer = handover.reservation.customer
        customer_name = f"{customer.first_name} {customer.last_name}".strip() or customer.email
        damage_items = _damage_line_items(handover.damage_notes)

        # Eksik yakıt da hasar gibi ayrı bir kalem olarak gösterilsin — kaç
        # puan eksik geldi ve bunun için gerçek maliyet ne (marjsız — bkz.
        # handovers/serializers.py _fuel_shortage_charge/DAMAGE_MARKUP_RATE,
        # müşteriden alınan tutardan kasıtlı olarak farklı). Delivery kaydı
        # olmayan (elle açılmış) talepler için 0 kalır.
        delivery = Handover.objects.filter(
            reservation=handover.reservation, type=HandoverType.DELIVERY
        ).first()
        fuel_shortage_percent = 0
        if delivery:
            fuel_shortage_percent = max(delivery.fuel_level - handover.fuel_level, 0)
        fuel_charge = _fuel_shortage_charge(fuel_shortage_percent)

        return {
            "customer_name": customer_name,
            "damage_summary": _damage_summary(handover.damage_notes),
            # Parça parça hasar + maliyet dökümü (Bakım Merkezi'ndeki Hasar
            # kutusunda tek satır yerine kalem kalem göstermek için).
            "damage_items": damage_items,
            "damage_total": sum(item["cost"] for item in damage_items),
            "fuel_shortage_percent": fuel_shortage_percent,
            "fuel_charge": fuel_charge,
            "is_dirty": handover.is_dirty,
            "returned_at": handover.created_at,
        }


class ServiceRequestCreateSerializer(serializers.ModelSerializer):
    """Write: yeni talep açma (SRV-1) — status/cost/assigned_to burada YOK,
    yeni bir talep her zaman 'open', maliyetsiz ve atamasız başlar."""

    class Meta:
        model = ServiceRequest
        fields = ["id", "vehicle", "request_type", "priority"]


class ServiceRequestUpdateSerializer(serializers.ModelSerializer):
    """Write: durum güncelleme + atama (SRV-2)."""

    class Meta:
        model = ServiceRequest
        fields = ["status", "assigned_to", "cost"]

    def validate_status(self, new_status):
        current_status = self.instance.status

        if new_status == current_status:
            return new_status

        allowed = ALLOWED_STATUS_TRANSITIONS[current_status]
        if new_status not in allowed:
            raise serializers.ValidationError(
                f"'{current_status}' durumundan '{new_status}' durumuna geçilemez."
            )

        return new_status

    def update(self, instance, validated_data):
        becomes_done = validated_data.get("status") == Status.DONE and instance.status != Status.DONE
        if becomes_done:
            instance.completed_at = timezone.now()
        instance = super().update(instance, validated_data)

        if becomes_done:
            # Araç bakımdayken açılmış BAŞKA bir açık talep yoksa (bkz.
            # handovers/serializers.py — hasar+yakıt aynı ziyarette TEK talep
            # açıyor ama elle ikinci bir talep de açılmış olabilir), araç
            # tekrar müsaite döner. Önceden burada hiçbir şey vehicle.status'u
            # geri almıyordu — "bakım tamamlandı" dense bile araç sonsuza
            # kadar MAINTENANCE'ta takılı kalıyordu.
            vehicle = instance.vehicle
            still_open = (
                ServiceRequest.active_objects.filter(
                    vehicle=vehicle, status__in=[Status.OPEN, Status.IN_PROGRESS]
                )
                .exclude(pk=instance.pk)
                .exists()
            )
            if not still_open and vehicle.status == VehicleStatus.MAINTENANCE:
                vehicle.status = VehicleStatus.AVAILABLE
                vehicle.save()

        return instance
