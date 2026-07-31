"""Tests for register/login — see PDF AUTH-1."""

import pytest

from users.helpers import Role
from users.models import User


@pytest.mark.django_db
class TestLogin:
    def test_login_success_returns_tokens(self, api_client, make_user):
        make_user(email="giris@fleet.com", password="SuperGucluSifre123!")

        response = api_client.post(
            "/api/auth/login",
            {"email": "giris@fleet.com", "password": "SuperGucluSifre123!"},
        )

        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data

    def test_login_wrong_password_fails(self, api_client, make_user):
        make_user(email="giris2@fleet.com", password="DogruSifre123!")

        response = api_client.post(
            "/api/auth/login",
            {"email": "giris2@fleet.com", "password": "YanlisSifre123!"},
        )

        assert response.status_code == 401

    def test_login_response_includes_role_claim(self, api_client, make_user):
        make_user(email="rol@fleet.com", password="SuperGucluSifre123!", role=Role.OPERATOR)

        response = api_client.post(
            "/api/auth/login",
            {"email": "rol@fleet.com", "password": "SuperGucluSifre123!"},
        )

        import base64
        import json

        payload = response.data["access"].split(".")[1]
        payload += "=" * (-len(payload) % 4)
        decoded = json.loads(base64.urlsafe_b64decode(payload))
        assert decoded["role"] == "operator"


@pytest.mark.django_db
class TestDriverList:
    def test_operator_can_list_drivers(self, authenticated_client, make_user):
        operator = make_user(email="driverlist-op@fleet.com", role=Role.OPERATOR)
        make_user(email="driverlist-cust@fleet.com")
        client = authenticated_client(operator)

        response = client.get("/api/auth/drivers")

        assert response.status_code == 200
        emails = [driver["email"] for driver in response.data]
        assert "driverlist-cust@fleet.com" in emails

    def test_driver_list_excludes_staff(self, authenticated_client, make_user):
        operator = make_user(email="driverlist-op2@fleet.com", role=Role.OPERATOR)
        make_user(email="driverlist-op3@fleet.com", role=Role.OPERATOR)
        client = authenticated_client(operator)

        response = client.get("/api/auth/drivers")

        emails = [driver["email"] for driver in response.data]
        assert "driverlist-op3@fleet.com" not in emails

    def test_customer_cannot_list_drivers(self, authenticated_client, make_user):
        client = authenticated_client(make_user(email="driverlist-cust2@fleet.com"))

        response = client.get("/api/auth/drivers")

        assert response.status_code == 403

    def test_operator_can_create_driver_without_password(self, authenticated_client, make_user):
        operator = make_user(email="drivercreate-op@fleet.com", role=Role.OPERATOR)
        client = authenticated_client(operator)

        response = client.post(
            "/api/auth/drivers",
            {"first_name": "Yeni", "last_name": "Sürücü", "email": "yenisurucu@fleet.com", "phone": "5551112233"},
        )

        assert response.status_code == 201
        driver = User.objects.get(email="yenisurucu@fleet.com")
        assert driver.role == Role.CUSTOMER
        # Şifre yok — bu hesapla hiçbir zaman giriş yapılamaz.
        assert driver.has_usable_password() is False

    def test_operator_can_set_driver_profile_on_create(self, authenticated_client, make_user):
        operator = make_user(email="drivercreate-op2@fleet.com", role=Role.OPERATOR)
        client = authenticated_client(operator)

        response = client.post(
            "/api/auth/drivers",
            {
                "first_name": "Ayşe",
                "last_name": "Yıl",
                "email": "aysedriver@fleet.com",
                "tc_no": "11122233344",
                "birth_date": "1990-01-01",
                "license_class": "B",
                "license_issue_date": "2012-01-01",
            },
        )

        assert response.status_code == 201
        assert response.data["is_profile_complete"] is True

    def test_operator_can_update_driver_profile(self, authenticated_client, make_user):
        operator = make_user(email="driverupdate-op@fleet.com", role=Role.OPERATOR)
        driver = make_user(email="driverupdate-cust@fleet.com", complete_profile=False)
        client = authenticated_client(operator)

        response = client.patch(
            f"/api/auth/drivers/{driver.id}",
            {
                "first_name": "Sürücü",
                "last_name": "Test",
                "tc_no": "99988877766",
                "birth_date": "1995-05-05",
                "license_class": "B",
                "license_issue_date": "2016-05-05",
            },
        )

        assert response.status_code == 200
        assert response.data["is_profile_complete"] is True

    def test_customer_cannot_create_driver(self, authenticated_client, make_user):
        client = authenticated_client(make_user(email="drivercreate-cust@fleet.com"))

        response = client.post(
            "/api/auth/drivers",
            {"first_name": "Test", "last_name": "Kullanıcı", "email": "baskacust@fleet.com"},
        )

        assert response.status_code == 403


@pytest.mark.django_db
class TestMe:
    def test_operator_can_view_own_account(self, authenticated_client, make_user):
        operator = make_user(email="hesabim@fleet.com", role=Role.OPERATOR)
        client = authenticated_client(operator)

        response = client.get("/api/auth/me")

        assert response.status_code == 200
        assert response.data["email"] == "hesabim@fleet.com"
        assert response.data["role"] == Role.OPERATOR


@pytest.mark.django_db
class TestStaffList:
    def test_operator_can_list_other_operators(self, authenticated_client, make_user):
        operator = make_user(email="staff-op@fleet.com", role=Role.OPERATOR)
        make_user(email="staff-op2@fleet.com", role=Role.OPERATOR)
        client = authenticated_client(operator)

        response = client.get("/api/auth/staff")

        assert response.status_code == 200
        emails = [staff["email"] for staff in response.data]
        assert "staff-op2@fleet.com" in emails

    def test_staff_list_excludes_customers(self, authenticated_client, make_user):
        operator = make_user(email="staff-op3@fleet.com", role=Role.OPERATOR)
        make_user(email="staff-cust@fleet.com")
        client = authenticated_client(operator)

        response = client.get("/api/auth/staff")

        emails = [staff["email"] for staff in response.data]
        assert "staff-cust@fleet.com" not in emails

    def test_customer_cannot_list_staff(self, authenticated_client, make_user):
        client = authenticated_client(make_user(email="staff-cust2@fleet.com"))

        response = client.get("/api/auth/staff")

        assert response.status_code == 403

    def test_operator_can_create_staff_with_real_password(self, authenticated_client, make_user):
        operator = make_user(email="staffcreate-op@fleet.com", role=Role.OPERATOR)
        client = authenticated_client(operator)

        response = client.post(
            "/api/auth/staff",
            {
                "first_name": "Yeni",
                "last_name": "Personel",
                "email": "yenipersonel@fleet.com",
                "password": "SuperGucluSifre123!",
            },
        )

        assert response.status_code == 201
        assert "password" not in response.data
        staff = User.objects.get(email="yenipersonel@fleet.com")
        assert staff.role == Role.OPERATOR
        # Sürücülerin aksine gerçek bir şifreyle giriş yapabilmeli.
        assert staff.has_usable_password() is True
        assert staff.check_password("SuperGucluSifre123!") is True

    def test_staff_create_requires_password(self, authenticated_client, make_user):
        operator = make_user(email="staffcreate-op2@fleet.com", role=Role.OPERATOR)
        client = authenticated_client(operator)

        response = client.post(
            "/api/auth/staff",
            {"first_name": "Yeni", "last_name": "Personel", "email": "sifresizpersonel@fleet.com"},
        )

        assert response.status_code == 400

    def test_customer_cannot_create_staff(self, authenticated_client, make_user):
        client = authenticated_client(make_user(email="staffcreate-cust@fleet.com"))

        response = client.post(
            "/api/auth/staff",
            {
                "first_name": "Test",
                "last_name": "Kullanıcı",
                "email": "baskapersonel@fleet.com",
                "password": "SuperGucluSifre123!",
            },
        )

        assert response.status_code == 403
