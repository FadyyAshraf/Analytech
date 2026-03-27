from django.urls import path
from . import views

urlpatterns = [
    path('', views.employee_dashboard, name='employee_dashboard'),

    path('list/', views.employee_list, name='employee_list'),
    path('create/', views.employee_create, name='employee_create'),
    path('<int:employee_id>/', views.employee_detail, name='employee_detail'),
    path('<int:employee_id>/edit/', views.employee_edit, name='employee_edit'),

    path('compensation/', views.compensation_list, name='compensation_list'),
    path('compensation/create/', views.compensation_create, name='compensation_create'),

    path('penalties/', views.penalty_list, name='penalty_list'),
    path('penalties/create/', views.penalty_create, name='penalty_create'),

    path('bonuses/', views.bonus_list, name='bonus_list'),
    path('bonuses/create/', views.bonus_create, name='bonus_create'),

    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/create/', views.expense_create, name='expense_create'),

    path('advances/', views.advance_list, name='advance_list'),
    path('advances/create/', views.advance_create, name='advance_create'),

    path('commissions/', views.commission_list, name='commission_list'),
    path('commissions/create/', views.commission_create, name='commission_create'),

    path('payrolls/', views.payroll_list, name='payroll_list'),
    path('payrolls/create/', views.payroll_create, name='payroll_create'),
]