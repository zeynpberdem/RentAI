"""Tests for handovers — see PDF HND-1/HND-2."""

from datetime import timedelta

import pytest
from django.utils import timezone

from reservations.helpers import Status as ReservationStatus
from reservations.models import Reservation
from service_requests.models import ServiceRequest
from users.helpers import Role


@pytest.mark.django_db
class TestDelivery:
    def test_delivery_activates_reservation(self, authenticated_client, make_user, reservation):
        operator = make_user(email="operator@fleet.com", role=Role.OPERATOR)
        client = authenticated_client(operator)

        response = client.post(
            "/api/handovers",
            {
                "reservation": str(reservation.id),
                "type": "delivery",
                "odometer_km": 10000,
                "fuel_level": 80,
            },
        )

        assert response.status_code == 201
        reservation.refresh_from_db()
        assert reservation.status == ReservationStatus.ACTIVE
        reservation.vehicle.refresh_from_db()
        assert reservation.vehicle.status == "rented"

    def test_second_delivery_for_same_reservation_fails(
        self, authenticated_client, make_user, reservation
    ):
        client = authenticated_client(make_user(email="op2@fleet.com", role=Role.OPERATOR))
        client.post(
            "/api/handovers",
            {"reservation": str(reservation.id), "type": "delivery", "odometer_km": 10000, "fuel_level": 80},
        )

        response = client.post(
            "/api/handovers",
            {"reservation": str(reservation.id), "type": "delivery", "odometer_km": 10000, "fuel_level": 80},
        )

        assert response.status_code == 400

    def test_non_operator_cannot_create_handover(self, authenticated_client, make_user, reservation):
        customer = make_user(email="cust@fleet.com", role=Role.CUSTOMER)
        client = authenticated_client(customer)

        response = client.post(
            "/api/handovers",
            {"reservation": str(reservation.id), "type": "delivery", "odometer_km": 10000, "fuel_level": 80},
        )

        assert response.status_code == 403


@pytest.mark.django_db
class TestReturn:
    def _deliver(self, client, reservation, fuel_level=80):
        return client.post(
            "/api/handovers",
            {
                "reservation": str(reservation.id),
                "type": "delivery",
                "odometer_km": 10000,
                "fuel_level": fuel_level,
            },
        )

    def test_return_before_delivery_fails(self, authenticated_client, make_user, reservation):
        client = authenticated_client(make_user(email="op3@fleet.com", role=Role.OPERATOR))

        response = client.post(
            "/api/handovers",
            {"reservation": str(reservation.id), "type": "return", "odometer_km": 10200, "fuel_level": 80},
        )

        assert response.status_code == 400

    def test_return_completes_reservation_and_charges_fuel_shortage(
        self, authenticated_client, make_user, reservation
    ):
        client = authenticated_client(make_user(email="op4@fleet.com", role=Role.OPERATOR))
        self._deliver(client, reservation, fuel_level=80)

        response = client.post(
            "/api/handovers",
            {"reservation": str(reservation.id), "type": "return", "odometer_km": 10200, "fuel_level": 60},
        )

        assert response.status_code == 201
        # 80 - 60 = 20 puan eksik yakıt * 20 TL = 400 TL gerçek maliyet,
        # müşteriden DAMAGE_MARKUP_RATE (1.25) ile 500 TL tahsil edilir
        # (bkz. handovers/serializers.py fuel_customer_charge).
        assert response.data["extra_charge"] == "500.00"
        reservation.refresh_from_db()
        assert reservation.status == ReservationStatus.COMPLETED
        reservation.vehicle.refresh_from_db()
        # Yakıt %100 değil (60) — ücreti alınsa bile araç fiziksel olarak
        # dolum bekliyor, doğrudan müsaite düşmüyor (bkz. servis talebi).
        assert reservation.vehicle.status == "maintenance"

    def test_return_with_no_fuel_shortage_has_no_charge(
        self, authenticated_client, make_user, reservation
    ):
        client = authenticated_client(make_user(email="op5@fleet.com", role=Role.OPERATOR))
        self._deliver(client, reservation, fuel_level=80)

        response = client.post(
            "/api/handovers",
            {"reservation": str(reservation.id), "type": "return", "odometer_km": 10200, "fuel_level": 80},
        )

        assert response.data["extra_charge"] == "0.00"

    def test_return_after_end_date_charges_late_fee(
        self, authenticated_client, make_user, vehicle
    ):
        customer = make_user(email="late-owner@example.com")
        today = timezone.localtime(timezone.now()).date()
        reservation = Reservation.objects.create(
            customer=customer,
            vehicle=vehicle,
            start_date=today - timedelta(days=5),
            end_date=today - timedelta(days=2),
            total_price=3000,
        )
        client = authenticated_client(make_user(email="op6@fleet.com", role=Role.OPERATOR))
        self._deliver(client, reservation, fuel_level=80)

        response = client.post(
            "/api/handovers",
            {"reservation": str(reservation.id), "type": "return", "odometer_km": 10200, "fuel_level": 80},
        )

        assert response.status_code == 201
        reservation.refresh_from_db()
        # 2 gün geç iade * 1000 TL günlük fiyat = 2000 TL ceza
        assert reservation.late_fee_amount == 2000
        assert reservation.early_return_discount == 0
        assert reservation.total_price == 5000

    def test_return_before_end_date_applies_early_discount(
        self, authenticated_client, make_user, vehicle
    ):
        customer = make_user(email="early-owner@example.com")
        today = timezone.localtime(timezone.now()).date()
        reservation = Reservation.objects.create(
            customer=customer,
            vehicle=vehicle,
            start_date=today - timedelta(days=2),
            end_date=today + timedelta(days=2),
            total_price=3000,
        )
        client = authenticated_client(make_user(email="op7@fleet.com", role=Role.OPERATOR))
        self._deliver(client, reservation, fuel_level=80)

        response = client.post(
            "/api/handovers",
            {"reservation": str(reservation.id), "type": "return", "odometer_km": 10200, "fuel_level": 80},
        )

        assert response.status_code == 201
        reservation.refresh_from_db()
        # 2 gün erken iade * 1000 TL günlük fiyat = 2000 TL indirim
        assert reservation.early_return_discount == 2000
        assert reservation.late_fee_amount == 0
        assert reservation.total_price == 1000

    def test_early_return_discount_does_not_exceed_total_price(
        self, authenticated_client, make_user, vehicle
    ):
        # Uç durum: 1 günlük bir rezervasyon, planlanan bitişten ÇOK önce
        # iade edilirse indirim, teslim/iade gününün ücretini (en az 1 günlük
        # daily_price) asla götürmemeli — bkz. serializers.py early_return_discount
        # cap yorumu. Bu yüzden burada total_price==daily_price olduğundan
        # indirim 0'a sınırlanır, total_price değişmeden kalır.
        customer = make_user(email="very-early-owner@example.com")
        today = timezone.localtime(timezone.now()).date()
        reservation = Reservation.objects.create(
            customer=customer,
            vehicle=vehicle,
            start_date=today,
            end_date=today + timedelta(days=1),
            total_price=1000,
        )
        client = authenticated_client(make_user(email="op8@fleet.com", role=Role.OPERATOR))
        self._deliver(client, reservation, fuel_level=80)

        response = client.post(
            "/api/handovers",
            {"reservation": str(reservation.id), "type": "return", "odometer_km": 10200, "fuel_level": 80},
        )

        assert response.status_code == 201
        reservation.refresh_from_db()
        assert reservation.early_return_discount == 0
        assert reservation.total_price == 1000

    def test_return_with_cosmetic_damage_opens_request_but_stays_available(
        self, authenticated_client, make_user, reservation
    ):
        # Hacer Hanım'ın isteği: çizik/sürtme/leke gibi kozmetik hasarlar
        # tek başına aracı sanayiye (Bakımda) düşürmesin — talep yine
        # otomatik açılır (kayıt için), ama araç Müsait kalır, operatör
        # isterse elle "Bakıma Al" der. Teslim/iade yakıtı bilerek %100 —
        # needs_refuel (fuel_level<100) tetiklenmesin, sadece hasar testi
        # izole edilsin (bkz. serializers.py create()).
        client = authenticated_client(make_user(email="op9@fleet.com", role=Role.OPERATOR))
        self._deliver(client, reservation, fuel_level=100)

        response = client.post(
            "/api/handovers",
            {
                "reservation": str(reservation.id),
                "type": "return",
                "odometer_km": 10200,
                "fuel_level": 100,
                "damage_notes": 'Hasarlar: Kaput (Çizik) ||JSON:{"hood":"scratch"}||',
            },
        )

        assert response.status_code == 201
        reservation.vehicle.refresh_from_db()
        assert reservation.vehicle.status == "available"
        request = ServiceRequest.objects.get(vehicle=reservation.vehicle)
        assert request.request_type == "maintenance"
        assert request.priority == "normal"
        # Kaput/scratch -> DAMAGE_REPAIR_COST tablosundan 500 TL.
        assert request.cost == 500

    def test_return_with_severe_damage_sets_vehicle_to_maintenance(
        self, authenticated_client, make_user, reservation
    ):
        # Çökme/eksik parça gibi ciddi hasarlar hâlâ aracı otomatik olarak
        # Bakımda'ya düşürür — araç fiilen yola çıkamayacak durumda.
        client = authenticated_client(make_user(email="op9b@fleet.com", role=Role.OPERATOR))
        self._deliver(client, reservation, fuel_level=80)

        response = client.post(
            "/api/handovers",
            {
                "reservation": str(reservation.id),
                "type": "return",
                "odometer_km": 10200,
                "fuel_level": 80,
                "damage_notes": 'Hasarlar: Ön Tampon (Çökme) ||JSON:{"front_bumper":"crash"}||',
            },
        )

        assert response.status_code == 201
        reservation.vehicle.refresh_from_db()
        assert reservation.vehicle.status == "maintenance"
        request = ServiceRequest.objects.get(vehicle=reservation.vehicle)
        assert request.request_type == "maintenance"
        assert request.priority == "high"
        # Ön tampon/crash -> DAMAGE_REPAIR_COST tablosundan 3000 TL.
        assert request.cost == 3000

    def test_return_with_no_damage_and_full_fuel_becomes_available(
        self, authenticated_client, make_user, reservation
    ):
        client = authenticated_client(make_user(email="op10@fleet.com", role=Role.OPERATOR))
        self._deliver(client, reservation, fuel_level=100)

        client.post(
            "/api/handovers",
            {
                "reservation": str(reservation.id),
                "type": "return",
                "odometer_km": 10200,
                "fuel_level": 100,
                "damage_notes": "Hasar Yok ||JSON:{}||",
            },
        )

        assert not ServiceRequest.objects.filter(vehicle=reservation.vehicle).exists()
        reservation.vehicle.refresh_from_db()
        assert reservation.vehicle.status == "available"

    def test_return_with_low_fuel_and_no_damage_opens_service_request(
        self, authenticated_client, make_user, reservation
    ):
        client = authenticated_client(make_user(email="op11@fleet.com", role=Role.OPERATOR))
        self._deliver(client, reservation, fuel_level=100)

        client.post(
            "/api/handovers",
            {
                "reservation": str(reservation.id),
                "type": "return",
                "odometer_km": 10200,
                "fuel_level": 70,
                "damage_notes": "Hasar Yok ||JSON:{}||",
            },
        )

        reservation.vehicle.refresh_from_db()
        assert reservation.vehicle.status == "maintenance"
        request = ServiceRequest.objects.get(vehicle=reservation.vehicle)
        assert request.request_type == "service"
        assert request.priority == "normal"