from django.urls import path
from . import views

urlpatterns = [
    path('sales/', views.sales_dashboard, name='sales_dashboard'),
    path('commissions/', views.commission_report, name='commission_report'),
]