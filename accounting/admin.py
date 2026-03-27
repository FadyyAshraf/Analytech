from django.contrib import admin
from .models import (
    Account,
    JournalEntry,
    JournalEntryLine,
    ReceiptVoucher,
    PaymentVoucher,
)


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'account_type', 'parent', 'is_active')
    list_filter = ('account_type', 'is_active')
    search_fields = ('code', 'name')
    ordering = ('code',)


class JournalEntryLineInline(admin.TabularInline):
    model = JournalEntryLine
    extra = 1


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ('id', 'entry_date', 'description', 'reference', 'status', 'total_debit', 'total_credit')
    list_filter = ('status', 'entry_date')
    search_fields = ('description', 'reference')
    inlines = [JournalEntryLineInline]


@admin.register(ReceiptVoucher)
class ReceiptVoucherAdmin(admin.ModelAdmin):
    list_display = ('id', 'voucher_date', 'customer', 'payer_name', 'amount', 'payment_method', 'reference', 'journal_entry')
    list_filter = ('payment_method', 'voucher_date')
    search_fields = ('payer_name', 'customer__name', 'reference', 'description')


@admin.register(PaymentVoucher)
class PaymentVoucherAdmin(admin.ModelAdmin):
    list_display = ('id', 'voucher_date', 'payee_name', 'amount', 'payment_method', 'reference', 'journal_entry')
    list_filter = ('payment_method', 'voucher_date')
    search_fields = ('payee_name', 'reference', 'description')