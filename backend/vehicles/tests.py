"""Tests for vehicle search/detail — see PDF VEH-2/VEH-3."""

import pytest

from vehicles.models import Vehicle


@pytest.mark.django_db
class TestVehicleList:
    def test_list_returns_vehicle(self, api_client, vehicle):
        response = api_client.get("/api/vehicles")

        assert response.status_code == 200
        assert response.data["count"] == 1

    def test_list_does_not_expose_plate(self, api_client, vehicle):
        response = api_client.get("/api/vehicles")

        # Plaka, herkese açık arama sonucunda bilerek gösterilmiyor
        # (bkz. vehicles/serializers.py).
        assert "plate" not in response.data["results"][0]

    def test_list_excludes_soft_deleted(self, api_client, vehicle):
        vehicle.is_active = False
        vehicle.save()

        response = api_client.get("/api/vehicles")

        assert response.data["count"] == 0

    def test_list_filters_by_segment(self, api_client, vehicle, location):
        Vehicle.objects.create(
            brand="Jeep", model="Compass", segment=Vehicle.Segment.SUV,
            transmission=Vehicle.Transmission.AUTOMATIC, fuel=Vehicle.Fuel.DIESEL,
            seats=5, plate="34SUV01", daily_price=2000, location=location,
        )

        response = api_client.get("/api/vehicles", {"segment": "suv"})

        assert response.data["count"] == 1
        assert response.data["results"][0]["brand"] == "Jeep"

    def test_list_filters_by_price_range(self, api_client, vehicle, location):
        Vehicle.objects.create(
            brand="Jeep", model="Compass", segment=Vehicle.Segment.SUV,
            transmission=Vehicle.Transmission.AUTOMATIC, fuel=Vehicle.Fuel.DIESEL,
            seats=5, plate="34SUV02", daily_price=2000, location=location,
        )

        # vehicle fixture'ı 1000 TL; sadece 1500 altını istiyoruz.
        response = api_client.get("/api/vehicles", {"daily_price_max": 1500})

        assert response.data["count"] == 1
        assert response.data["results"][0]["brand"] == "Toyota"


@pytest.mark.django_db
class TestVehicleDetail:
    def test_detail_returns_vehicle(self, api_client, vehicle):
        response = api_client.get(f"/api/vehicles/{vehicle.id}")

        assert response.status_code == 200
        assert response.data["brand"] == "Toyota"

    def test_detail_not_found_returns_404(self, api_client):
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = api_client.get(f"/api/vehicles/{fake_id}")

        assert response.status_code == 404
