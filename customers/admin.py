from django.contrib import admin
from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'customer_type',
        'phone',
        'contact_person',
    )
    search_fields = (
        'name',
        'phone',
        'contact_person',
    )
    list_filter = (
        'customer_type',
    )