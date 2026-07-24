"""
Ortak test fixture'ları — testler arasında tekrar eden hazırlık kodu
(kullanıcı oluşturma, giriş yapmış istemci, örnek araç) burada toplanır.
"""

import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from reservations.models import Reservation
from users.helpers import Role
from users.models import User
from vehicles.helpers import Fuel, Segment, Transmission
from vehicles.models import Location, Vehicle


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def make_user(db):
    """Belirli bir role sahip kullanıcı oluşturan bir fabrika (factory) döner."""

    def _make_user(email="user@example.com", password="TestSifre123!", role=Role.CUSTOMER):
        return User.objects.create_user(email=email, password=password, role=role)

    return _make_user


@pytest.fixture
def authenticated_client(api_client):
    """Verilen kullanıcı için JWT üretip istemciye ekleyen bir fabrika döner."""

    def _authenticated_client(user):
        access_token = RefreshToken.for_user(user).access_token
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        return api_client

    return _authenticated_client


@pytest.fixture
def location(db):
    return Location.objects.create(name="Test Şube", city="Istanbul")


@pytest.fixture
def vehicle(db, location):
    return Vehicle.objects.create(
        brand="Toyota",
        model="Corolla",
        segment=Segment.MID,
        transmission=Transmission.AUTOMATIC,
        fuel=Fuel.PETROL,
        seats=5,
        plate="34TEST01",
        daily_price=1000,
        location=location,
    )


@pytest.fixture
def reservation(db, vehicle, make_user):
    customer = make_user(email="reservation-owner@example.com")
    return Reservation.objects.create(
        customer=customer,
        vehicle=vehicle,
        start_date="2026-08-05",
        end_date="2026-08-08",
        total_price=3000,
    )
