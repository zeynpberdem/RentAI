"""Serializers for the public vehicle search API — see PDF GET /api/vehicles."""

from rest_framework import serializers

from .helpers import Fuel, Transmission
from .models import Location, Vehicle


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ["id", "name", "city"]


class VehicleSerializer(serializers.ModelSerializer):
    # location, Vehicle tablosunda sadece bir id (sayı) olarak duruyor;
    # nested serializer kullanarak onu "id: 3" yerine "{id, name, city}"
    # şeklinde, daha kullanışlı bir JSON olarak gösteriyoruz.
    location = LocationSerializer(read_only=True)

    class Meta:
        model = Vehicle
        # "plate" BİLEREK burada YOK — herkese açık arama sonucunda
        # plaka gibi operasyonel bir bilgiyi göstermeye gerek yok.
        fields = [
            "id",
            "brand",
            "model",
            "segment",
            "transmission",
            "fuel",
            "seats",
            "daily_price",
            "status",
            "location",
            "image",
            "has_ac",
            "is_4wd",
        ]


class VehicleWriteSerializer(serializers.ModelSerializer):
    """Admin araç ekleme/düzenleme (VEH-1) — plaka ve şube burada YAZILABİLİR
    (public VehicleSerializer'da plate bilerek yoktu, ama admin bunu görüp
    girebilmeli)."""

    class Meta:
        model = Vehicle
        fields = [
            "id",
            "brand",
            "model",
            "segment",
            "transmission",
            "fuel",
            "seats",
            "plate",
            "daily_price",
            "status",
            "location",
            "image",
            "has_ac",
            "is_4wd",
        ]

    def validate(self, attrs):
        # PATCH'te (kısmi güncelleme) sadece değişen alan attrs'te olur —
        # değişmeyen tarafı, var olan kayıttan (self.instance) okuyoruz.
        fuel = attrs.get("fuel", getattr(self.instance, "fuel", None))
        transmission = attrs.get("transmission", getattr(self.instance, "transmission", None))

        if fuel == Fuel.ELECTRIC and transmission == Transmission.MANUAL:
            raise serializers.ValidationError("Elektrikli araçların manuel vitesi olamaz.")

        return attrs
