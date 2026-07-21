from django.contrib import admin

from .models import Location, Vehicle


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "city")
    search_fields = ("name", "city")


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ("plate", "brand", "model", "segment", "status", "daily_price", "location")
    list_filter = ("segment", "transmission", "fuel", "status", "location")
    search_fields = ("plate", "brand", "model")