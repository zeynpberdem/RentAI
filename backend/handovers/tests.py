"""Tests for handovers — see PDF HND-1/HND-2."""

import pytest

from reservations.models import Reservation
from users.models import User


@pytest.mark.django_db
class TestDelivery:
    def test_delivery_activates_reservation(self, authenticated_client, make_user, reservation):
        operator = make_user(email="operator@fleet.com", role=User.Role.OPERATOR)
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
        assert reservation.status == Reservation.Status.ACTIVE

    def test_second_delivery_for_same_reservation_fails(
        self, authenticated_client, make_user, reservation
    ):
        client = authenticated_client(make_user(email="op2@fleet.com", role=User.Role.OPERATOR))
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
        customer = make_user(email="cust@fleet.com", role=User.Role.CUSTOMER)
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
        client = authenticated_client(make_user(email="op3@fleet.com", role=User.Role.OPERATOR))

        response = client.post(
            "/api/handovers",
            {"reservation": str(reservation.id), "type": "return", "odometer_km": 10200, "fuel_level": 80},
        )

        assert response.status_code == 400

    def test_return_completes_reservation_and_charges_fuel_shortage(
        self, authenticated_client, make_user, reservation
    ):
        client = authenticated_client(make_user(email="op4@fleet.com", role=User.Role.OPERATOR))
        self._deliver(client, reservation, fuel_level=80)

        response = client.post(
            "/api/handovers",
            {"reservation": str(reservation.id), "type": "return", "odometer_km": 10200, "fuel_level": 60},
        )

        assert response.status_code == 201
        # 80 - 60 = 20 puan eksik yakıt * 20 TL = 400 TL
        assert response.data["extra_charge"] == "400.00"
        reservation.refresh_from_db()
        assert reservation.status == Reservation.Status.COMPLETED

    def test_return_with_no_fuel_shortage_has_no_charge(
        self, authenticated_client, make_user, reservation
    ):
        client = authenticated_client(make_user(email="op5@fleet.com", role=User.Role.OPERATOR))
        self._deliver(client, reservation, fuel_level=80)

        response = client.post(
            "/api/handovers",
            {"reservation": str(reservation.id), "type": "return", "odometer_km": 10200, "fuel_level": 80},
        )

        assert response.data["extra_charge"] == "0.00"