from django import forms
from django.contrib import admin, messages
from .models import InventoryItem, InventoryTransaction, InventoryLot, RecallNotice


class InventoryTransactionAdminForm(forms.ModelForm):
    class Meta:
        model = InventoryTransaction
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if 'item' in self.fields:
            self.fields['item'].label_from_instance = (
                lambda obj: f"{obj.item_name} — رصيد: {obj.quantity}"
            )

        if 'lot' in self.fields:
            self.fields['lot'].label_from_instance = (
                lambda obj: f"{obj.lot_number} — متاح: {obj.quantity}"
            )


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = (
        'item_name',
        'item_code',
        'item_type',
        'quantity',
        'min_stock',
        'low_stock_status',
        'unit',
        'supplier',
    )
    search_fields = (
        'item_name',
        'item_code',
        'supplier',
    )
    list_filter = (
        'item_type',
        'supplier',
    )

    def low_stock_status(self, obj):
        if obj.is_below_min():
            return "⚠️ منخفض"
        return "✔️ طبيعي"

    low_stock_status.short_description = 'الحالة'


@admin.register(InventoryLot)
class InventoryLotAdmin(admin.ModelAdmin):
    list_display = (
        'item',
        'lot_number',
        'quantity',
        'expiry_date',
        'expiry_status',
    )
    search_fields = (
        'item__item_name',
        'lot_number',
    )
    list_filter = (
        'expiry_date',
    )

    def expiry_status(self, obj):
        if obj.is_expired():
            return "❌ منتهي"
        if obj.is_expiring_soon():
            return "⚠️ قرب الانتهاء"
        return "✔️ صالح"

    expiry_status.short_description = 'الحالة'


@admin.register(RecallNotice)
class RecallNoticeAdmin(admin.ModelAdmin):
    list_display = (
        'recall_number',
        'item',
        'lot',
        'notice_date',
        'risk_level',
        'status',
    )
    search_fields = (
        'recall_number',
        'item__item_name',
        'lot__lot_number',
    )
    list_filter = (
        'risk_level',
        'status',
        'notice_date',
    )


@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    form = InventoryTransactionAdminForm

    list_display = (
        'item',
        'lot',
        'transaction_type',
        'source_type',
        'source_name',
        'quantity',
        'balance_before',
        'balance_after',
        'transaction_date',
    )
    search_fields = (
        'item__item_name',
        'item__item_code',
        'source_name',
        'reference',
    )
    list_filter = (
        'transaction_type',
        'source_type',
        'transaction_date',
    )

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if obj.item.quantity <= obj.item.min_stock:
            messages.warning(
                request,
                f"تحذير: رصيد الصنف '{obj.item.item_name}' أصبح منخفضًا ({obj.item.quantity})"
            )