from rest_framework import serializers
from users.serializers import UserListSerializer  # UserSerializer yerine UserListSerializer yaptık
from vehicles.serializers import VehicleSerializer, LocationSerializer
from .models import Reservations2

class Reservation2Serializer(serializers.ModelSerializer):
    customer_detail = UserListSerializer(source='customer', read_only=True)
    vehicle_detail = VehicleSerializer(source='vehicle', read_only=True)
    pickup_location_detail = LocationSerializer(source='pickup_location', read_only=True)
    return_location_detail = LocationSerializer(source='return_location', read_only=True)
    class Meta:
        model = Reservations2
        fields = [
            'id',
            'customer',
            'customer_detail',
            'vehicle', #kıralana aracın ıd numarası
            'vehicle_detail',#aracın sıpp kodu adı soyadı e postası
            'pickup_location',
            'pickup_location_detail',#şubelerin tam adları
            'return_location',
            'return_location_detail',
            'reservation_type',#rezervasyon tipi
            'source',
            'start_date',
            'end_date',
            'created_at',
        ]