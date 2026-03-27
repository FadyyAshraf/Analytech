from django.urls import path
from . import views

urlpatterns = [
    path('', views.invoice_list, name='invoice_list'),
    path('create/', views.invoice_create, name='invoice_create'),
    path('<int:invoice_id>/', views.invoice_detail, name='invoice_detail'),
    path('<int:invoice_id>/print/', views.invoice_print, name='invoice_print'),
    path('item-meta/<int:item_id>/', views.item_meta, name='invoice_item_meta'),

    path('from-quotation/<int:quotation_id>/', views.create_invoice_from_quotation, name='create_invoice_from_quotation'),
    path('<int:invoice_id>/post/', views.post_invoice, name='post_invoice'),
    path('<int:invoice_id>/cancel/', views.cancel_invoice, name='cancel_invoice'),
]