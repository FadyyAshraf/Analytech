from django.contrib import admin
from .models import SalesOrder, SalesOrderItem


class SalesOrderItemInline(admin.TabularInline):
    model = SalesOrderItem
    extra = 1


@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'customer',
        'order_date',
        'status',
        'payment_terms',
        'delivery_method',
        'sales_owner',
        'subtotal',
        'invoice',
    )
    list_filter = ('status', 'payment_terms', 'delivery_method', 'order_date')
    search_fields = ('customer__name', 'id', 'tracking_number')
    inlines = [SalesOrderItemInline]


@admin.register(SalesOrderItem)
class SalesOrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'item', 'quantity', 'qty_released', 'price', 'total')
    search_fields = ('order__id', 'item__item_name')