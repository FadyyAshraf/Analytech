from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Invoice, InvoiceItem, InvoicePrintSettings


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    fields = ('item', 'lot', 'quantity', 'price', 'total')
    readonly_fields = ('total',)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'customer_name',
        'invoice_date',
        'subtotal',
        'discount_percent',
        'discount_amount',
        'net_before_vat',
        'vat_amount',
        'total_after_vat',
        'print_link',
    )
    inlines = [InvoiceItemInline]

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.recalculate_totals()

    def print_link(self, obj):
        url = reverse('invoice_print', args=[obj.id])
        return format_html('<a href="{}" target="_blank">طباعة</a>', url)

    print_link.short_description = 'طباعة'


@admin.register(InvoicePrintSettings)
class InvoicePrintSettingsAdmin(admin.ModelAdmin):
    list_display = ('id', 'logo')
    fields = ('logo', 'footer_text_ar', 'footer_text_en')