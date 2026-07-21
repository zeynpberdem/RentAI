"""
Role-based permission classes.

These check the already-authenticated request.user.role (set by our
custom User model) — they do NOT check the JWT itself, that part is
already handled by JWTAuthentication (see settings.py
DEFAULT_AUTHENTICATION_CLASSES). By the time has_permission() runs,
request.user is already a real User instance (or an AnonymousUser if
no valid token was sent).
"""

from rest_framework.permissions import BasePermission


class HasRole(BasePermission):
    """Base class — subclasses just set `required_role`, no repeated logic."""

    required_role = None

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == self.required_role
        )


class IsCustomer(HasRole):
    """Allows access only to authenticated users with role == customer."""

    required_role = "customer"


class IsOperator(HasRole):
    """Allows access only to authenticated users with role == operator."""

    required_role = "operator"


class IsAdmin(HasRole):
    """Allows access only to authenticated users with role == admin."""

    required_role = "admin"
