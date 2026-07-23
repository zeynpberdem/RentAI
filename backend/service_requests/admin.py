from django.contrib import admin

from .models import ServiceRequest


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ("vehicle", "request_type", "priority", "status", "cost", "assigned_to")
    list_filter = ("request_type", "priority", "status")
