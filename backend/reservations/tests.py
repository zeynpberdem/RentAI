"""Tests for reservations — see PDF RES-1/2/3."""

from datetime import timedelta

import pytest
from django.utils import timezone

from reservations.helpers import Status
from reservations.models import Reservation
from users.helpers import Role


@pytest.mark.django_db
class TestReservationCreate:
    def test_create_reservation_calculates_price(self, authenticated_client, make_user, vehicle):
        client = authenticated_client(make_user())

        response = client.post(
            "/api/reservations",
            {"vehicle": str(vehicle.id), "start_date": "2026-08-05", "end_date": "2026-08-08"},
        )

        assert response.status_code == 201
        reservation = Reservation.objects.get(id=response.data["id"])
        # 3 gün * 1000 TL (vehicle fixture'ının günlük fiyatı)
        assert reservation.total_price == 3000

    def test_pickup_and_return_location_default_to_vehicle_location(self, authenticated_client, make_user, vehicle):
        client = authenticated_client(make_user())

        response = client.post(
            "/api/reservations",
            {"vehicle": str(vehicle.id), "start_date": "2026-08-05", "end_date": "2026-08-08"},
        )

        assert response.status_code == 201
        reservation = Reservation.objects.get(id=response.data["id"])
        assert reservation.pickup_location_id == vehicle.location_id
        assert reservation.return_location_id == vehicle.location_id

    def test_can_choose_different_return_location(self, authenticated_client, make_user, vehicle):
        from vehicles.models import Location

        other_location = Location.objects.create(name="Sabiha Gökçen Şube", city="Istanbul")
        client = authenticated_client(make_user())

        response = client.post(
            "/api/reservations",
            {
                "vehicle": str(vehicle.id),
                "start_date": "2026-08-05",
                "end_date": "2026-08-08",
                "return_location": str(other_location.id),
            },
        )

        assert response.status_code == 201
        reservation = Reservation.objects.get(id=response.data["id"])
        assert reservation.pickup_location_id == vehicle.location_id
        assert reservation.return_location_id == other_location.id

    def test_reservation_type_and_source_can_be_set(self, authenticated_client, make_user, vehicle):
        client = authenticated_client(make_user())

        response = client.post(
            "/api/reservations",
            {
                "vehicle": str(vehicle.id),
                "start_date": "2026-08-05",
                "end_date": "2026-08-08",
                "type": "corporate",
                "source": "call_center",
            },
        )

        assert response.status_code == 201
        assert response.data["type"] == "corporate"
        assert response.data["source"] == "call_center"

    def test_reservation_type_and_source_default(self, authenticated_client, make_user, vehicle):
        client = authenticated_client(make_user())

        response = client.post(
            "/api/reservations",
            {"vehicle": str(vehicle.id), "start_date": "2026-08-05", "end_date": "2026-08-08"},
        )

        assert response.status_code == 201
        assert response.data["type"] == "short_term"
        assert response.data["source"] == "branch"

    def test_overlapping_dates_rejected(self, authenticated_client, make_user, vehicle):
        client = authenticated_client(make_user())
        client.post(
            "/api/reservations",
            {"vehicle": str(vehicle.id), "start_date": "2026-08-05", "end_date": "2026-08-08"},
        )

        response = client.post(
            "/api/reservations",
            {"vehicle": str(vehicle.id), "start_date": "2026-08-06", "end_date": "2026-08-10"},
        )

        assert response.status_code == 400

    def test_same_customer_cannot_book_overlapping_different_vehicle(
        self, authenticated_client, make_user, vehicle
    ):
        from vehicles.models import Vehicle

        other_vehicle = Vehicle.objects.create(
            brand=vehicle.brand,
            model=vehicle.model,
            segment=vehicle.segment,
            transmission=vehicle.transmission,
            fuel=vehicle.fuel,
            seats=vehicle.seats,
            plate="34TEST02",
            daily_price=vehicle.daily_price,
            location=vehicle.location,
        )
        client = authenticated_client(make_user())
        client.post(
            "/api/reservations",
            {"vehicle": str(vehicle.id), "start_date": "2026-08-05", "end_date": "2026-08-08"},
        )

        # Farklı araç, ama aynı müşteri ve çakışan tarih — bir kişi aynı
        # anda iki araç kullanamaz.
        response = client.post(
            "/api/reservations",
            {"vehicle": str(other_vehicle.id), "start_date": "2026-08-06", "end_date": "2026-08-10"},
        )

        assert response.status_code == 400

    def test_cancelled_reservation_does_not_block_dates(self, authenticated_client, make_user, vehicle):
        client = authenticated_client(make_user())
        first = client.post(
            "/api/reservations",
            {"vehicle": str(vehicle.id), "start_date": "2026-08-05", "end_date": "2026-08-08"},
        )
        client.post(f"/api/reservations/{first.data['id']}/cancel")

        response = client.post(
            "/api/reservations",
            {"vehicle": str(vehicle.id), "start_date": "2026-08-06", "end_date": "2026-08-10"},
        )

        assert response.status_code == 201

    def test_incomplete_profile_cannot_create_reservation(self, authenticated_client, make_user, vehicle):
        client = authenticated_client(make_user(complete_profile=False))

        response = client.post(
            "/api/reservations",
            {"vehicle": str(vehicle.id), "start_date": "2026-08-05", "end_date": "2026-08-08"},
        )

        assert response.status_code == 400

    def test_operator_can_create_reservation_for_driver(self, authenticated_client, make_user, vehicle):
        operator = make_user(email="operator@fleet.com", role=Role.OPERATOR)
        driver = make_user(email="driver@fleet.com")
        client = authenticated_client(operator)

        response = client.post(
            "/api/reservations",
            {
                "customer": str(driver.id),
                "vehicle": str(vehicle.id),
                "start_date": "2026-08-05",
                "end_date": "2026-08-08",
            },
        )

        assert response.status_code == 201
        assert Reservation.objects.get(id=response.data["id"]).customer == driver

    def test_operator_reservation_requires_customer_field(self, authenticated_client, make_user, vehicle):
        operator = make_user(email="operator2@fleet.com", role=Role.OPERATOR)
        client = authenticated_client(operator)

        response = client.post(
            "/api/reservations",
            {"vehicle": str(vehicle.id), "start_date": "2026-08-05", "end_date": "2026-08-08"},
        )

        assert response.status_code == 400

    def test_operator_cannot_pick_a_non_customer_as_driver(self, authenticated_client, make_user, vehicle):
        operator = make_user(email="operator3@fleet.com", role=Role.OPERATOR)
        other_operator = make_user(email="operator4@fleet.com", role=Role.OPERATOR)
        client = authenticated_client(operator)

        response = client.post(
            "/api/reservations",
            {
                "customer": str(other_operator.id),
                "vehicle": str(vehicle.id),
                "start_date": "2026-08-05",
                "end_date": "2026-08-08",
            },
        )

        assert response.status_code == 400

    def test_unauthenticated_cannot_create_reservation_for_driver(self, api_client, make_user, vehicle):
        driver = make_user(email="driver2@fleet.com")

        response = api_client.post(
            "/api/reservations",
            {
                "customer": str(driver.id),
                "vehicle": str(vehicle.id),
                "start_date": "2026-08-05",
                "end_date": "2026-08-08",
            },
        )

        assert response.status_code == 401


@pytest.mark.django_db
class TestReservationListAndCancel:
    def test_list_only_shows_own_reservations(self, authenticated_client, make_user, vehicle):
        owner = make_user(email="owner@fleet.com")
        other = make_user(email="other@fleet.com")
        authenticated_client(owner).post(
            "/api/reservations",
            {"vehicle": str(vehicle.id), "start_date": "2026-08-05", "end_date": "2026-08-08"},
        )

        response = authenticated_client(other).get("/api/reservations")

        assert response.data["count"] == 0

    def test_cancel_other_users_reservation_returns_404(self, authenticated_client, make_user, vehicle):
        owner = make_user(email="owner2@fleet.com")
        other = make_user(email="other2@fleet.com")
        created = authenticated_client(owner).post(
            "/api/reservations",
            {"vehicle": str(vehicle.id), "start_date": "2026-08-05", "end_date": "2026-08-08"},
        )

        response = authenticated_client(other).post(
            f"/api/reservations/{created.data['id']}/cancel"
        )

        assert response.status_code == 404

    def test_cancel_already_cancelled_fails(self, authenticated_client, make_user, vehicle):
        client = authenticated_client(make_user())
        created = client.post(
            "/api/reservations",
            {"vehicle": str(vehicle.id), "start_date": "2026-08-05", "end_date": "2026-08-08"},
        )
        client.post(f"/api/reservations/{created.data['id']}/cancel")

        response = client.post(f"/api/reservations/{created.data['id']}/cancel")

        assert response.status_code == 400

    def test_list_filters_by_status(self, authenticated_client, make_user, vehicle):
        # Tarihler timezone.now()'a göre (sabit takvim tarihi DEĞİL): sabit bir
        # tarih olsaydı zaman ilerledikçe geçmişte kalır, no-show otomatik
        # iptali (bkz. views.cancel_noshow_reservations) rezervasyonu bu test
        # elle iptal etmeden önce iptal ederdi.
        client = authenticated_client(make_user())
        start = timezone.now() + timedelta(days=5)
        end = start + timedelta(days=3)
        cancelled = client.post(
            "/api/reservations",
            {"vehicle": str(vehicle.id), "start_date": str(start.date()), "end_date": str(end.date())},
        )
        client.post(f"/api/reservations/{cancelled.data['id']}/cancel")
        other_start = start + timedelta(days=30)
        other_end = other_start + timedelta(days=3)
        client.post(
            "/api/reservations",
            {"vehicle": str(vehicle.id), "start_date": str(other_start.date()), "end_date": str(other_end.date())},
        )

        # status artık metin değil sayısal kod (bkz. helpers.Status) — filtre
        # de serializer çıktısı da bu kodu kullanıyor.
        response = client.get("/api/reservations", {"status": Status.CANCELLED})

        assert response.data["count"] == 1
        assert response.data["results"][0]["status"] == Status.CANCELLED
