from django.contrib import admin

from .models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("customer", "vehicle", "start_date", "end_date", "status", "total_price")
    list_filter = ("status",)
    search_fields = ("customer__email", "vehicle__plate")
