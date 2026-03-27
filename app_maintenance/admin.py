from django.contrib import admin
from .models import (
    MaintenanceRequest,
    PreventiveMaintenancePlan,
    MaintenanceVisit,
    MaintenanceRequirement,
)


class MaintenanceRequirementInline(admin.TabularInline):
    model = MaintenanceRequirement
    extra = 1


@admin.register(MaintenanceRequest)
class MaintenanceRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'device', 'request_date', 'priority', 'status')
    list_filter = ('priority', 'status')
    search_fields = ('customer__name', 'device__device_name', 'device__serial_number', 'reported_by')


@admin.register(PreventiveMaintenancePlan)
class PreventiveMaintenancePlanAdmin(admin.ModelAdmin):
    list_display = ('device', 'customer', 'interval_type', 'last_visit_date', 'next_due_date', 'is_active')
    list_filter = ('interval_type', 'is_active')
    search_fields = ('device__device_name', 'device__serial_number', 'customer__name')


@admin.register(MaintenanceVisit)
class MaintenanceVisitAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'device', 'visit_type', 'status', 'visit_date', 'engineer')
    list_filter = ('visit_type', 'status', 'visit_date')
    search_fields = (
        'customer__name',
        'device__device_name',
        'device__serial_number',
        'engineer__full_name',
        'engineer_name',
    )
    inlines = [MaintenanceRequirementInline]


@admin.register(MaintenanceRequirement)
class MaintenanceRequirementAdmin(admin.ModelAdmin):
    list_display = ('visit', 'item', 'quantity', 'availability_status', 'quotation_status', 'approved_by_customer', 'installed')
    list_filter = ('availability_status', 'quotation_status', 'approved_by_customer', 'installed')
    search_fields = ('visit__customer__name', 'visit__device__device_name', 'item__item_name')