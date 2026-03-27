from django.contrib import admin
from .models import (
    Employee,
    EmployeeRole,
    EmployeeCompensation,
    EmployeePenalty,
    EmployeeBonus,
    EmployeeExpenseClaim,
    EmployeeAdvance,
    EmployeeCommission,
    EmployeePayroll,
)


class EmployeeRoleInline(admin.TabularInline):
    model = EmployeeRole
    extra = 1


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        'employee_code',
        'full_name',
        'department',
        'job_title',
        'status',
        'hire_date',
        'phone',
        'can_do_sales',
        'can_do_service',
        'sales_commission_percent',
    )
    list_filter = ('status', 'department', 'can_do_sales', 'can_do_service')
    search_fields = ('employee_code', 'full_name', 'phone', 'national_id')
    inlines = [EmployeeRoleInline]


@admin.register(EmployeeCompensation)
class EmployeeCompensationAdmin(admin.ModelAdmin):
    list_display = ('employee', 'basic_salary', 'payment_method', 'effective_from', 'is_active')
    list_filter = ('payment_method', 'is_active')
    search_fields = ('employee__full_name', 'employee__employee_code')


@admin.register(EmployeePenalty)
class EmployeePenaltyAdmin(admin.ModelAdmin):
    list_display = ('employee', 'penalty_date', 'amount', 'reason')
    list_filter = ('penalty_date',)
    search_fields = ('employee__full_name', 'reason')


@admin.register(EmployeeBonus)
class EmployeeBonusAdmin(admin.ModelAdmin):
    list_display = ('employee', 'bonus_date', 'amount', 'reason')
    list_filter = ('bonus_date',)
    search_fields = ('employee__full_name', 'reason')


@admin.register(EmployeeExpenseClaim)
class EmployeeExpenseClaimAdmin(admin.ModelAdmin):
    list_display = ('employee', 'expense_date', 'amount', 'expense_type', 'approved')
    list_filter = ('expense_type', 'approved', 'expense_date')
    search_fields = ('employee__full_name', 'description')


@admin.register(EmployeeAdvance)
class EmployeeAdvanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'advance_date', 'amount', 'settled_amount', 'remaining_amount')
    list_filter = ('advance_date',)
    search_fields = ('employee__full_name', 'description')


@admin.register(EmployeeCommission)
class EmployeeCommissionAdmin(admin.ModelAdmin):
    list_display = ('employee', 'commission_date', 'customer', 'invoice', 'base_amount', 'commission_percent', 'commission_amount', 'status')
    list_filter = ('status', 'commission_date')
    search_fields = ('employee__full_name', 'customer__name')


@admin.register(EmployeePayroll)
class EmployeePayrollAdmin(admin.ModelAdmin):
    list_display = ('employee', 'month', 'year', 'net_salary', 'status')
    list_filter = ('month', 'year', 'status')
    search_fields = ('employee__full_name',)