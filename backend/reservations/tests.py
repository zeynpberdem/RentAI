"""Tests for reservations — see PDF RES-1/2/3."""

import pytest

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

    def test_non_customer_cannot_create_reservation(self, authenticated_client, make_user, vehicle):
        operator = make_user(email="operator@fleet.com", role=Role.OPERATOR)
        client = authenticated_client(operator)

        response = client.post(
            "/api/reservations",
            {"vehicle": str(vehicle.id), "start_date": "2026-08-05", "end_date": "2026-08-08"},
        )

        assert response.status_code == 403


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
        client = authenticated_client(make_user())
        cancelled = client.post(
            "/api/reservations",
            {"vehicle": str(vehicle.id), "start_date": "2026-08-05", "end_date": "2026-08-08"},
        )
        client.post(f"/api/reservations/{cancelled.data['id']}/cancel")
        client.post(
            "/api/reservations",
            {"vehicle": str(vehicle.id), "start_date": "2026-09-05", "end_date": "2026-09-08"},
        )

        response = client.get("/api/reservations", {"status": "cancelled"})

        assert response.data["count"] == 1
        assert response.data["results"][0]["status"] == "cancelled"
