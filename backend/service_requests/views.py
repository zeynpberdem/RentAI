"""Views for service requests — see PDF SRV-1/SRV-2."""

from rest_framework import mixins, viewsets

from users.permissions import IsOperator

from .models import ServiceRequest
from .serializers import (
    ServiceRequestCreateSerializer,
    ServiceRequestSerializer,
    ServiceRequestUpdateSerializer,
)


class ServiceRequestViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    GET         /api/service-requests      -> tüm talepleri listele (SRV-1)
    POST        /api/service-requests      -> yeni talep aç (SRV-1)
    PUT/PATCH   /api/service-requests/{id} -> durum güncelleme + atama (SRV-2)

    Sadece list/create/update var — retrieve/destroy bilerek yok, çünkü
    PDF'in istediği işlemler bunlardan ibaret (bir talep elle silinmez,
    durumu 'cancelled' yapılır).
    """

    queryset = ServiceRequest.active_objects.select_related("vehicle", "vehicle__location")
    permission_classes = [IsOperator]

    def get_serializer_class(self):
        if self.action == "create":
            return ServiceRequestCreateSerializer
        if self.action in ("update", "partial_update"):
            return ServiceRequestUpdateSerializer
        return ServiceRequestSerializer
