from django.urls import path
from . import views

urlpatterns = [
    path('', views.sales_order_list, name='sales_order_list'),
    path('create/', views.sales_order_create, name='sales_order_create'),
    path('<int:order_id>/', views.sales_order_detail, name='sales_order_detail'),

    path('<int:order_id>/confirm/', views.sales_order_confirm, name='sales_order_confirm'),
    path('<int:order_id>/release/', views.sales_order_release, name='sales_order_release'),
    path('<int:order_id>/ship/', views.sales_order_ship, name='sales_order_ship'),
    path('<int:order_id>/deliver/', views.sales_order_deliver, name='sales_order_deliver'),
    path('<int:order_id>/close/', views.sales_order_close, name='sales_order_close'),
    path('<int:order_id>/create-invoice/', views.create_invoice_from_sales_order, name='create_invoice_from_sales_order'),
]