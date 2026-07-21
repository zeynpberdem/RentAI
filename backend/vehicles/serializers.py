"""Serializers for the public vehicle search API — see PDF GET /api/vehicles."""

from rest_framework import serializers

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
        ]
