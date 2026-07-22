"""Serializers for reservations — see PDF RES-1/2/3."""

from rest_framework import serializers

from vehicles.serializers import VehicleSerializer

from .models import Reservation


class ReservationSerializer(serializers.ModelSerializer):
    """Read-only: liste/detay görünümünde araç bilgisi tam olarak gösterilir."""

    vehicle = VehicleSerializer(read_only=True)

    class Meta:
        model = Reservation
        fields = [
            "id",
            "vehicle",
            "start_date",
            "end_date",
            "status",
            "total_price",
            "pricing_snapshot",
        ]


class ReservationCreateSerializer(serializers.ModelSerializer):
    """Write-only: müşteri sadece araç ve tarih seçer, geri kalanı biz hesaplarız."""

    class Meta:
        model = Reservation
        fields = ["id", "vehicle", "start_date", "end_date"]
        # "customer" bilerek burada YOK: müşteri kendi adına değil de
        # başka birinin adına rezervasyon açamasın diye — customer,
        # view içinde request.user'dan set edilecek (bkz. views.py).
        # "status"/"total_price" de burada YOK: bunlar sistem tarafından
        # hesaplanır, müşteri elle bir fiyat/durum gönderemez.

    def validate(self, attrs):
        start = attrs["start_date"]
        end = attrs["end_date"]
        if end <= start:
            raise serializers.ValidationError("end_date, start_date'ten sonra olmalı.")

        # Müsaitlik kontrolü: aynı araç için, tarihleri çakışan ve hâlâ
        # geçerli (iptal/tamamlanmamış) başka bir rezervasyon var mı?
        # Çakışma formülü: mevcut.start < yeni.end VE mevcut.end > yeni.start
        conflicting = Reservation.objects.filter(
            vehicle=attrs["vehicle"],
            start_date__lt=end,
            end_date__gt=start,
        ).exclude(status__in=[Reservation.Status.CANCELLED, Reservation.Status.COMPLETED])

        if conflicting.exists():
            raise serializers.ValidationError(
                "Bu araç, seçilen tarih aralığında müsait değil."
            )

        return attrs

    def create(self, validated_data):
        vehicle = validated_data["vehicle"]
        days = (validated_data["end_date"] - validated_data["start_date"]).days
        total_price = vehicle.daily_price * days

        validated_data["total_price"] = total_price
        validated_data["pricing_snapshot"] = {
            "daily_price": str(vehicle.daily_price),
            "days": days,
            "total_price": str(total_price),
        }
        return super().create(validated_data)