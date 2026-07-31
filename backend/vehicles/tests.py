"""Tests for vehicle search/detail — see PDF VEH-2/VEH-3."""

import pytest

from users.helpers import Role
from vehicles.helpers import Fuel, Segment, Transmission
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
            brand="Jeep", model="Compass", segment=Segment.SUV,
            transmission=Transmission.AUTOMATIC, fuel=Fuel.DIESEL,
            seats=5, plate="34SUV01", daily_price=2000, location=location,
        )

        response = api_client.get("/api/vehicles", {"segment": "suv"})

        assert response.data["count"] == 1
        assert response.data["results"][0]["brand"] == "Jeep"

    def test_list_filters_by_price_range(self, api_client, vehicle, location):
        Vehicle.objects.create(
            brand="Jeep", model="Compass", segment=Segment.SUV,
            transmission=Transmission.AUTOMATIC, fuel=Fuel.DIESEL,
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


@pytest.mark.django_db
class TestVehicleAdminCRUD:
    def _payload(self, location):
        return {
            "brand": "Renault",
            "model": "Clio",
            "segment": "economy",
            "transmission": "manual",
            "fuel": "petrol",
            "seats": 5,
            "plate": "34NEW01",
            "daily_price": 800,
            "location": str(location.id),
        }

    def test_admin_can_create_vehicle(self, authenticated_client, make_user, location):
        admin = make_user(email="admin@fleet.com", role=Role.ADMIN)
        client = authenticated_client(admin)

        response = client.post("/api/vehicles", self._payload(location))

        assert response.status_code == 201
        assert Vehicle.objects.filter(plate="34NEW01").exists()

    def test_admin_can_set_sipp_code(self, authenticated_client, make_user, location):
        admin = make_user(email="admin-sipp@fleet.com", role=Role.ADMIN)
        client = authenticated_client(admin)

        payload = {**self._payload(location), "sipp_code": "CDMR"}
        response = client.post("/api/vehicles", payload)

        assert response.status_code == 201
        assert Vehicle.objects.get(plate="34NEW01").sipp_code == "CDMR"

    def test_staff_view_includes_sipp_code(self, authenticated_client, make_user, vehicle):
        vehicle.sipp_code = "EDAR"
        vehicle.save()
        operator = make_user(email="operator-sipp@fleet.com", role=Role.OPERATOR)
        client = authenticated_client(operator)

        response = client.get("/api/vehicles")

        result = next(v for v in response.data["results"] if v["id"] == str(vehicle.id))
        assert result["sipp_code"] == "EDAR"

    def test_non_admin_cannot_create_vehicle(self, authenticated_client, make_user, location):
        operator = make_user(email="operator@fleet.com", role=Role.OPERATOR)
        client = authenticated_client(operator)

        response = client.post("/api/vehicles", self._payload(location))

        assert response.status_code == 403

    def test_unauthenticated_cannot_create_vehicle(self, api_client, location):
        response = api_client.post("/api/vehicles", self._payload(location))

        assert response.status_code in (401, 403)

    def test_admin_can_update_vehicle(self, authenticated_client, make_user, vehicle):
        admin = make_user(email="admin2@fleet.com", role=Role.ADMIN)
        client = authenticated_client(admin)

        response = client.patch(
            f"/api/vehicles/{vehicle.id}", {"daily_price": "1500.00"}, format="json"
        )

        assert response.status_code == 200
        vehicle.refresh_from_db()
        assert vehicle.daily_price == 1500

    def test_admin_delete_soft_deletes(self, authenticated_client, make_user, vehicle):
        admin = make_user(email="admin3@fleet.com", role=Role.ADMIN)
        client = authenticated_client(admin)

        response = client.delete(f"/api/vehicles/{vehicle.id}")

        assert response.status_code == 204
        vehicle.refresh_from_db()
        # Gerçekten silinmedi, sadece pasif hale getirildi.
        assert vehicle.is_active is False
        assert Vehicle.objects.filter(id=vehicle.id).exists()

    def test_electric_manual_combination_rejected(self, authenticated_client, make_user, location):
        admin = make_user(email="admin4@fleet.com", role=Role.ADMIN)
        client = authenticated_client(admin)
        payload = self._payload(location)
        payload["fuel"] = "electric"
        payload["transmission"] = "manual"

        response = client.post("/api/vehicles", payload)

        assert response.status_code == 400
        assert not Vehicle.objects.filter(plate=payload["plate"]).exists()


