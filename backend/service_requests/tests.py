"""Tests for service requests — see PDF SRV-1/SRV-2."""

import pytest

from service_requests.models import ServiceRequest
from users.models import User


@pytest.mark.django_db
class TestServiceRequestCreate:
    def test_create_defaults_to_open(self, authenticated_client, make_user, vehicle):
        operator = make_user(email="op@fleet.com", role=User.Role.OPERATOR)
        client = authenticated_client(operator)

        response = client.post(
            "/api/service-requests",
            {"vehicle": str(vehicle.id), "request_type": "maintenance", "priority": "high"},
        )

        assert response.status_code == 201
        request = ServiceRequest.objects.get(id=response.data["id"])
        assert request.status == ServiceRequest.Status.OPEN
        assert request.cost == 0
        assert request.assigned_to is None

    def test_non_operator_cannot_create(self, authenticated_client, make_user, vehicle):
        customer = make_user(email="cust@fleet.com", role=User.Role.CUSTOMER)
        client = authenticated_client(customer)

        response = client.post(
            "/api/service-requests",
            {"vehicle": str(vehicle.id), "request_type": "wash", "priority": "low"},
        )

        assert response.status_code == 403


@pytest.mark.django_db
class TestServiceRequestUpdate:
    def _make_request(self, operator, vehicle, status=ServiceRequest.Status.OPEN):
        return ServiceRequest.objects.create(
            vehicle=vehicle,
            request_type=ServiceRequest.RequestType.MAINTENANCE,
            priority=ServiceRequest.Priority.NORMAL,
            status=status,
        )

    def test_valid_transition_open_to_in_progress(self, authenticated_client, make_user, vehicle):
        operator = make_user(email="op2@fleet.com", role=User.Role.OPERATOR)
        client = authenticated_client(operator)
        request = self._make_request(operator, vehicle)

        response = client.patch(
            f"/api/service-requests/{request.id}", {"status": "in_progress"}, format="json"
        )

        assert response.status_code == 200
        request.refresh_from_db()
        assert request.status == ServiceRequest.Status.IN_PROGRESS

    def test_invalid_transition_open_to_done_rejected(self, authenticated_client, make_user, vehicle):
        operator = make_user(email="op3@fleet.com", role=User.Role.OPERATOR)
        client = authenticated_client(operator)
        request = self._make_request(operator, vehicle)

        response = client.patch(
            f"/api/service-requests/{request.id}", {"status": "done"}, format="json"
        )

        assert response.status_code == 400

    def test_done_is_a_terminal_state(self, authenticated_client, make_user, vehicle):
        operator = make_user(email="op4@fleet.com", role=User.Role.OPERATOR)
        client = authenticated_client(operator)
        request = self._make_request(operator, vehicle, status=ServiceRequest.Status.DONE)

        response = client.patch(
            f"/api/service-requests/{request.id}", {"status": "open"}, format="json"
        )

        assert response.status_code == 400

    def test_assign_operator(self, authenticated_client, make_user, vehicle):
        creator = make_user(email="op5@fleet.com", role=User.Role.OPERATOR)
        assignee = make_user(email="op6@fleet.com", role=User.Role.OPERATOR)
        client = authenticated_client(creator)
        request = self._make_request(creator, vehicle)

        response = client.patch(
            f"/api/service-requests/{request.id}",
            {"assigned_to": str(assignee.id)},
            format="json",
        )

        assert response.status_code == 200
        request.refresh_from_db()
        assert request.assigned_to_id == assignee.id
