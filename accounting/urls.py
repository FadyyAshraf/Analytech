from django.urls import path
from . import views

urlpatterns = [
    path('', views.accounting_dashboard, name='accounting_dashboard'),

    path('accounts/', views.account_list, name='account_list'),
    path('accounts/create/', views.account_create, name='account_create'),
    path('accounts/<int:account_id>/edit/', views.account_edit, name='account_edit'),

    path('journal/', views.journal_entry_list, name='journal_entry_list'),
    path('journal/create/', views.journal_entry_create, name='journal_entry_create'),
    path('journal/<int:entry_id>/', views.journal_entry_detail, name='journal_entry_detail'),
    path('journal/<int:entry_id>/post/', views.journal_entry_post, name='journal_entry_post'),
    path('journal/<int:entry_id>/cancel/', views.journal_entry_cancel, name='journal_entry_cancel'),

    path('receipts/', views.receipt_voucher_list, name='receipt_voucher_list'),
    path('receipts/create/', views.receipt_voucher_create, name='receipt_voucher_create'),
    path('receipts/<int:voucher_id>/edit/', views.receipt_voucher_edit, name='receipt_voucher_edit'),
    path('receipts/<int:voucher_id>/delete/', views.receipt_voucher_delete, name='receipt_voucher_delete'),

    path('payments/', views.payment_voucher_list, name='payment_voucher_list'),
    path('payments/create/', views.payment_voucher_create, name='payment_voucher_create'),
    path('payments/<int:voucher_id>/edit/', views.payment_voucher_edit, name='payment_voucher_edit'),
    path('payments/<int:voucher_id>/delete/', views.payment_voucher_delete, name='payment_voucher_delete'),

    path('customer-statement/', views.customer_statement, name='customer_statement'),
    path('ledger/', views.account_ledger, name='account_ledger'),
    path('trial-balance/', views.trial_balance_report, name='trial_balance_report'),
    path('profit-loss/', views.profit_loss_report, name='profit_loss_report'),
]