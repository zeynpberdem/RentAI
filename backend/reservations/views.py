"""Views for reservations — see PDF RES-1/2/3."""

from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsCustomer

from .models import Reservation
from .serializers import ReservationCreateSerializer, ReservationSerializer


class ReservationListCreateView(generics.ListCreateAPIView):
    """
    GET /api/reservations  -> müşteri sadece KENDİ rezervasyonlarını görür (RES-3)
    POST /api/reservations -> müşteri kendi adına rezervasyon açar (RES-1)
    """

    permission_classes = [IsCustomer]
    # RES-3: ?status=cancelled gibi bir sorgu parametresiyle filtreleme.
    # Zaten kurulu DjangoFilterBackend (settings.py) sayesinde, özel bir
    # FilterSet yazmaya gerek kalmadan tek satırla eşitlik filtresi kurulur.
    filterset_fields = ["status"]

    def get_serializer_class(self):
        # Okuma (liste) ve yazma (oluşturma) için farklı serializer kullanıyoruz:
        # okumada araç bilgisini tam gösteriyoruz, yazmada müşteri sadece
        # araç id'si + tarih gönderiyor.
        if self.request.method == "POST":
            return ReservationCreateSerializer
        return ReservationSerializer

    def get_queryset(self):
        return (
            Reservation.active_objects.filter(customer=self.request.user)
            .select_related("vehicle", "vehicle__location")
        )

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

        if reservation.status in (Reservation.Status.CANCELLED, Reservation.Status.COMPLETED):
            return Response(
                {"detail": "Bu rezervasyon zaten iptal edilmiş ya da tamamlanmış."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reservation.status = Reservation.Status.CANCELLED
        reservation.save()
        return Response(ReservationSerializer(reservation).data)
