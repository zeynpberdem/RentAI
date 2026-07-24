"""Views for reservations — see PDF RES-1/2/3."""

from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsCustomer, IsOperator

from .helpers import Status
from .models import Reservation
from .serializers import ReservationCreateSerializer, ReservationSerializer


class ReservationListCreateView(generics.ListCreateAPIView):
    """
    GET /api/reservations  -> müşteri KENDİ rezervasyonlarını (RES-3),
                               operatör TÜM rezervasyonları görür (teslim/iade
                               kaydı açarken doğru rezervasyonu bulabilsin diye).
    POST /api/reservations -> sadece müşteri, kendi adına rezervasyon açar (RES-1)
    """

    # RES-3: ?status=cancelled gibi bir sorgu parametresiyle filtreleme.
    # Zaten kurulu DjangoFilterBackend (settings.py) sayesinde, özel bir
    # FilterSet yazmaya gerek kalmadan tek satırla eşitlik filtresi kurulur.
    filterset_fields = ["status"]

    def get_permissions(self):
        # Oluşturma sadece müşterinin işi; operatör kimin adına olduğunu
        # belirleyip başkası adına rezervasyon açamamalı.
        if self.request.method == "POST":
            return [IsCustomer()]
        return [(IsCustomer | IsOperator)()]

    def get_serializer_class(self):
        # Okuma (liste) ve yazma (oluşturma) için farklı serializer kullanıyoruz:
        # okumada araç bilgisini tam gösteriyoruz, yazmada müşteri sadece
        # araç id'si + tarih gönderiyor.
        if self.request.method == "POST":
            return ReservationCreateSerializer
        return ReservationSerializer

    def get_queryset(self):
        queryset = Reservation.active_objects.select_related("vehicle", "vehicle__location")
        if self.request.user.role == "operator":
            return queryset
        return queryset.filter(customer=self.request.user)

    def perform_create(self, serializer):
        # customer, istekte gönderilmez — her zaman giriş yapmış kullanıcının
        # kendisi olur. Böylece biri başkasının adına rezervasyon açamaz.
        serializer.save(customer=self.request.user)


class ReservationCancelView(APIView):
    """POST /api/reservations/{id}/cancel — kendi rezervasyonunu iptal et (RES-2)."""

    permission_classes = [IsCustomer]

    def post(self, request, pk):
        # customer=request.user filtresi: başkasının rezervasyon ID'sini
        # denerse "yok" (404) döner — "var ama senin değil" (403) demek,
        # o rezervasyonun varlığını ifşa eder, bu yüzden 404 tercih ettik.
        reservation = get_object_or_404(
            Reservation.active_objects, pk=pk, customer=request.user
        )

        if reservation.status in (Status.CANCELLED, Status.COMPLETED):
            return Response(
                {"detail": "Bu rezervasyon zaten iptal edilmiş ya da tamamlanmış."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reservation.status = Status.CANCELLED
        reservation.save()
        return Response(ReservationSerializer(reservation).data)
