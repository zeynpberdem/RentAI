"""Views for service requests — see PDF SRV-1/SRV-2."""

from rest_framework import generics

from users.permissions import IsOperator

from .models import ServiceRequest
from .serializers import (
    ServiceRequestCreateSerializer,
    ServiceRequestSerializer,
    ServiceRequestUpdateSerializer,
)


class ServiceRequestListCreateView(generics.ListCreateAPIView):
    """
    GET /api/service-requests  -> tüm talepleri listele (SRV-1)
    POST /api/service-requests -> yeni talep aç (SRV-1)
    """

    queryset = ServiceRequest.active_objects.select_related("vehicle", "vehicle__location")
    permission_classes = [IsOperator]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ServiceRequestCreateSerializer
        return ServiceRequestSerializer


class ServiceRequestUpdateView(generics.UpdateAPIView):
    """PATCH /api/service-requests/{id} — durum güncelleme + atama (SRV-2)."""

    queryset = ServiceRequest.active_objects.all()
    serializer_class = ServiceRequestUpdateSerializer
    permission_classes = [IsOperator]
