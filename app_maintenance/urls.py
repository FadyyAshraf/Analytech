from django.urls import path
from . import views

urlpatterns = [
    path('requests/', views.maintenance_request_list, name='maintenance_request_list'),
    path('requests/create/', views.maintenance_request_create, name='maintenance_request_create'),
    path('requests/<int:request_id>/edit/', views.maintenance_request_edit, name='maintenance_request_edit'),

    path('plans/', views.preventive_plan_list, name='preventive_plan_list'),
    path('plans/create/', views.preventive_plan_create, name='preventive_plan_create'),
    path('plans/<int:plan_id>/edit/', views.preventive_plan_edit, name='preventive_plan_edit'),
    path('plans/sync/', views.preventive_plan_sync, name='preventive_plan_sync'),

    path('visits/', views.maintenance_visit_list, name='maintenance_visit_list'),
    path('visits/create/', views.maintenance_visit_create, name='maintenance_visit_create'),
    path('visits/<int:visit_id>/edit/', views.maintenance_visit_edit, name='maintenance_visit_edit'),

    path('reports/', views.maintenance_reports_dashboard, name='maintenance_reports_dashboard'),
    path('reports/overdue-preventive/', views.overdue_preventive_customers_report, name='overdue_preventive_customers_report'),
    path('reports/completed-preventive/', views.completed_preventive_customers_report, name='completed_preventive_customers_report'),
    path('reports/engineers/', views.engineer_performance_report, name='engineer_performance_report'),
]