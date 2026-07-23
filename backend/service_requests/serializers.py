"""Serializers for service requests — see PDF SRV-1/SRV-2."""

from rest_framework import serializers

from vehicles.serializers import VehicleSerializer

from .models import ServiceRequest

# Bir durumdan hangi durumlara geçilebileceğinin haritası. Boş küme = son
# durum, buradan başka hiçbir yere geçilemez.
ALLOWED_STATUS_TRANSITIONS = {
    ServiceRequest.Status.OPEN: {ServiceRequest.Status.IN_PROGRESS, ServiceRequest.Status.CANCELLED},
    ServiceRequest.Status.IN_PROGRESS: {ServiceRequest.Status.DONE, ServiceRequest.Status.CANCELLED},
    ServiceRequest.Status.DONE: set(),
    ServiceRequest.Status.CANCELLED: set(),
}


class ServiceRequestSerializer(serializers.ModelSerializer):
    """Read-only: liste/detay görünümü, araç bilgisi tam gösterilir."""

    vehicle = VehicleSerializer(read_only=True)

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
        ]


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
