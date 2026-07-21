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


class IsCustomer(BasePermission):
    """Allows access only to authenticated users with role == customer."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "customer"
        )


class IsOperator(BasePermission):
    """Allows access only to authenticated users with role == operator."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "operator"
        )


class IsAdmin(BasePermission):
    """Allows access only to authenticated users with role == admin."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "admin"
        )