from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """
    Django'nun hazır UserAdmin'i "username" alanına göre kurulu; email
    tabanlı modelimiz için fieldsets/add_fieldsets'i baştan tanımlıyoruz.
    """

    ordering = ("-created_at",)
    list_display = ("email", "role", "is_active", "is_staff", "created_at")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("email", "phone")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("phone", "role")}),
        (
            "Permissions",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Important dates", {"fields": ("last_login", "created_at", "updated_at")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "role", "password1", "password2"),
            },
        ),
    )
    readonly_fields = ("created_at", "updated_at", "last_login")