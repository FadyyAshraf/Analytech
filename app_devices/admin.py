from django.contrib import admin
from .models import Device


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = (
        'device_name',
        'customer',
        'device_type',
        'model',
        'serial_number',
    )
    search_fields = (
        'device_name',
        'serial_number',
        'model',
        'customer__name',
    )
    list_filter = (
        'device_type',
    )