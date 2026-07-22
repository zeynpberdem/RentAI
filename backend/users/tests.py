"""Tests for register/login — see PDF AUTH-1."""

import pytest

from users.models import User


@pytest.mark.django_db
class TestRegister:
    def test_register_creates_customer(self, api_client):
        response = api_client.post(
            "/api/auth/register",
            {"email": "yeni@fleet.com", "password": "SuperGucluSifre123!", "phone": "5551112233"},
        )

        assert response.status_code == 201
        # Şifre response'da asla görünmemeli.
        assert "password" not in response.data

        user = User.objects.get(email="yeni@fleet.com")
        # Kayıt sırasında role gönderilmedi, varsayılan customer olmalı.
        assert user.role == User.Role.CUSTOMER
        # Şifre hash'lenmiş olmalı, düz metin olarak SAKLANMAMALI.
        assert user.password != "SuperGucluSifre123!"

    def test_register_duplicate_email_fails(self, api_client, make_user):
        make_user(email="var@fleet.com")

        response = api_client.post(
            "/api/auth/register",
            {"email": "var@fleet.com", "password": "SuperGucluSifre123!"},
        )

        assert response.status_code == 400


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
