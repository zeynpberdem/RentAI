"""Serializers for the public vehicle search API — see PDF GET /api/vehicles."""

from rest_framework import serializers

# reservations.models (sadece model, serializer değil) — reservations app'i zaten
# vehicles.models'a bağımlı (Reservation.vehicle FK'si), bu yön (vehicles ->
# reservations.models) için döngüsel import riski yok.
from reservations.models import Reservation

from .helpers import Fuel, Transmission
from .models import Location, Vehicle


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ["id", "name", "city", "latitude", "longitude"]


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


class VehicleStaffSerializer(VehicleSerializer):
    """Operatör/admin görünümü — plaka burada VAR, çünkü personel fiziksel
    aracı tanımak için plakaya ihtiyaç duyar (herkese açık VehicleSerializer'da
    bilerek yoktu)."""

    class Meta(VehicleSerializer.Meta):
        fields = VehicleSerializer.Meta.fields + ["plate", "sipp_code"]


class VehicleCalendarReservationSerializer(serializers.ModelSerializer):
    """Rezervasyon Takvimi ekranındaki yalın rezervasyon görünümü — araç
    bilgisi BİLEREK YOK: bu serializer zaten VehicleCalendarSerializer'ın
    (aracın kendisinin) altında nested olarak kullanılıyor, aracı bir de
    burada tekrar gömmek aynı veriyi iki kere ağdan taşımak olurdu."""

    customer_name = serializers.SerializerMethodField()

    class Meta:
        model = Reservation
        fields = ["id", "start_date", "end_date", "status", "customer_name"]

    def get_customer_name(self, reservation):
        full_name = f"{reservation.customer.first_name} {reservation.customer.last_name}".strip()
        return full_name or reservation.customer.email


class VehicleCalendarSerializer(serializers.ModelSerializer):
    """GET /api/vehicles/calendar — her satır bir araç, verilen tarih
    aralığıyla kesişen rezervasyonlarıyla birlikte TEK istekte gelir.

    "reservations" alanı, view'da prefetch_related(Prefetch(..., to_attr=
    "calendar_reservations")) ile önceden yüklenmiş listeyi okur — burada
    ayrıca bir sorgu ATILMAZ (N+1 olmaz).
    """

    reservations = VehicleCalendarReservationSerializer(source="calendar_reservations", many=True, read_only=True)

    class Meta:
        model = Vehicle
        fields = ["id", "plate", "brand", "model", "reservations"]


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
            "sipp_code",
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
