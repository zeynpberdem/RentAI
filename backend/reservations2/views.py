from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Reservations2
from .serializers import Reservation2Serializer


class Reservation2ViewSet(viewsets.ModelViewSet):
    queryset = Reservations2.objects.select_related(
        "customer", "vehicle", "pickup_location", "return_location"
    )
    serializer_class = Reservation2Serializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["reservation_type", "source"]
