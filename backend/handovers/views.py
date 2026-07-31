"""Views for handovers — see PDF HND-1/HND-2."""

from rest_framework import mixins, viewsets

from users.permissions import IsOperator

from .models import Handover
from .serializers import HandoverListSerializer, HandoverSerializer


class HandoverViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    GET  /api/handovers -> Teslimat Listesi ekranı (?type=delivery ile sadece
                            teslimler, ?type=return ile sadece iadeler)
    POST /api/handovers -> teslim (delivery) ya da iade (return) kaydı

    retrieve/update/destroy bilerek yok — PDF'in istediği işlemler bunlardan
    ibaret (bir teslim/iade kaydı sonradan değiştirilmez ya da silinmez).
    """

    queryset = Handover.objects.select_related(
        "reservation", "reservation__vehicle", "reservation__customer"
    )
    permission_classes = [IsOperator]

    def get_serializer_class(self):
        return HandoverSerializer if self.action == "create" else HandoverListSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        handover_type = self.request.query_params.get("type")
        if handover_type:
            queryset = queryset.filter(type=handover_type)
        return queryset

    def perform_create(self, serializer):
        # created_user: bu teslim/iade işlemini hangi operatörün yaptığının
        # kaydı (BaseModel'in audit alanı burada gerçekten işe yarıyor).
        serializer.save(created_user=self.request.user)
