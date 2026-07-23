from django.contrib import admin

from .models import Handover


@admin.register(Handover)
class HandoverAdmin(admin.ModelAdmin):
    list_display = ("reservation", "type", "odometer_km", "fuel_level", "extra_charge", "created_at")
    list_filter = ("type",)