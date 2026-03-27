from django.urls import path
from .views import (
    inventory_dashboard,
    item_list,
    item_create,
    item_edit,
    lot_list,
    lot_create,
    lot_edit,
    transaction_list,
    transaction_create,
    recall_list,
    recall_create,
    item_lots_api,
)

urlpatterns = [
    path('', inventory_dashboard, name='inventory_dashboard'),

    path('items/', item_list, name='inventory_item_list'),
    path('items/new/', item_create, name='inventory_item_create'),
    path('items/<int:item_id>/edit/', item_edit, name='inventory_item_edit'),

    path('lots/', lot_list, name='inventory_lot_list'),
    path('lots/new/', lot_create, name='inventory_lot_create'),
    path('lots/<int:lot_id>/edit/', lot_edit, name='inventory_lot_edit'),

    path('transactions/', transaction_list, name='inventory_transaction_list'),
    path('transactions/create/', transaction_create, name='inventory_transaction_create'),

    path('recalls/', recall_list, name='inventory_recall_list'),
    path('recalls/create/', recall_create, name='inventory_recall_create'),

    path('api/item/<int:item_id>/lots/', item_lots_api, name='inventory_item_lots_api'),
]