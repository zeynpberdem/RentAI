"""Serializer for handovers — see PDF HND-1/HND-2."""

from rest_framework import serializers

from reservations.helpers import Status as ReservationStatus

from .helpers import Type
from .models import Handover

# Yakıt eksiği başına (yüzde puanı) ücret. Basit, sabit bir oran — PDF
# tam bir formül vermiyor, gerçek kiralama sitelerindeki yaygın pratiğe
# (eksik yakıt + servis ücreti) uygun, en basit hâliyle uyguladık.
FUEL_SHORTAGE_RATE_PER_PERCENT = 20


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

        else:  # RETURN
            # Teslim kaydındaki yakıt seviyesiyle kıyaslıyoruz — eksikse
            # ek ücret hesaplanır, fazlaysa/aynıysa ücret alınmaz.
            delivery = Handover.objects.get(
                reservation=reservation, type=Type.DELIVERY
            )
            fuel_shortage = delivery.fuel_level - validated_data["fuel_level"]
            if fuel_shortage > 0:
                validated_data["extra_charge"] = fuel_shortage * FUEL_SHORTAGE_RATE_PER_PERCENT

            reservation.status = ReservationStatus.COMPLETED
            reservation.save()

        return super().create(validated_data)