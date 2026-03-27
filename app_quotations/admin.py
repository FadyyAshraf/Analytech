from django.contrib import admin
from .models import Quotation, QuotationItem


class QuotationItemInline(admin.TabularInline):
    model = QuotationItem
    extra = 1
    fields = (
        'item_type',
        'inventory_item',
        'maintenance_requirement',
        'description',
        'quantity',
        'price',
        'total',
    )
    readonly_fields = ('total',)


@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'display_customer',
        'quotation_type',
        'status',
        'quotation_date',
        'total_after_vat',
    )
    list_filter = ('quotation_type', 'status')
    search_fields = (
        'customer__name',
        'customer_name_manual',
        'reference',
        'subject',
    )
    readonly_fields = (
        'subtotal',
        'discount_amount',
        'net_before_vat',
        'vat_amount',
        'total_after_vat',
    )
    fields = (
        'customer',
        'customer_name_manual',
        'customer_phone_manual',
        'customer_address_manual',
        'contact_person_manual',
        'device',
        'quotation_type',
        'status',
        'quotation_date',
        'valid_until',
        'reference',
        'subject',
        'maintenance_request',
        'maintenance_visit',
        'discount_percent',
        'vat_percent',
        'subtotal',
        'discount_amount',
        'net_before_vat',
        'vat_amount',
        'total_after_vat',
        'notes',
        'terms',
    )
    inlines = [QuotationItemInline]

    def display_customer(self, obj):
        return obj.display_customer_name
    display_customer.short_description = 'العميل'

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.recalculate_totals()


@admin.register(QuotationItem)
class QuotationItemAdmin(admin.ModelAdmin):
    list_display = ('quotation', 'description', 'quantity', 'price', 'total')