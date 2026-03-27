from django import forms

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


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            'employee_code',
            'full_name',
            'department',
            'job_title',
            'status',
            'hire_date',
            'birth_date',
            'national_id',
            'phone',
            'email',
            'address',
            'qualification',
            'specialization',
            'direct_manager',
            'can_do_sales',
            'can_do_service',
            'can_manage_team',
            'sales_commission_percent',
            'notes',
        ]
        widgets = {
            'employee_code': forms.TextInput(attrs={'class': 'form-control'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'job_title': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'hire_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'national_id': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'qualification': forms.TextInput(attrs={'class': 'form-control'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'direct_manager': forms.Select(attrs={'class': 'form-control'}),
            'sales_commission_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class EmployeeRoleForm(forms.ModelForm):
    class Meta:
        model = EmployeeRole
        fields = ['employee', 'role_name', 'is_active', 'notes']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-control'}),
            'role_name': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class EmployeeCompensationForm(forms.ModelForm):
    class Meta:
        model = EmployeeCompensation
        fields = [
            'employee',
            'basic_salary',
            'transport_allowance',
            'phone_allowance',
            'housing_allowance',
            'other_allowances',
            'payment_method',
            'bank_name',
            'bank_account',
            'effective_from',
            'is_active',
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-control'}),
            'basic_salary': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'transport_allowance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'phone_allowance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'housing_allowance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'other_allowances': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'bank_name': forms.TextInput(attrs={'class': 'form-control'}),
            'bank_account': forms.TextInput(attrs={'class': 'form-control'}),
            'effective_from': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class EmployeePenaltyForm(forms.ModelForm):
    class Meta:
        model = EmployeePenalty
        fields = ['employee', 'penalty_date', 'amount', 'reason', 'notes']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-control'}),
            'penalty_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'reason': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class EmployeeBonusForm(forms.ModelForm):
    class Meta:
        model = EmployeeBonus
        fields = ['employee', 'bonus_date', 'amount', 'reason', 'notes']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-control'}),
            'bonus_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'reason': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class EmployeeExpenseClaimForm(forms.ModelForm):
    class Meta:
        model = EmployeeExpenseClaim
        fields = ['employee', 'expense_date', 'amount', 'expense_type', 'description', 'approved', 'notes']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-control'}),
            'expense_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'expense_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class EmployeeAdvanceForm(forms.ModelForm):
    class Meta:
        model = EmployeeAdvance
        fields = ['employee', 'advance_date', 'amount', 'description', 'settled_amount', 'notes']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-control'}),
            'advance_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'settled_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class EmployeeCommissionForm(forms.ModelForm):
    class Meta:
        model = EmployeeCommission
        fields = [
            'employee',
            'customer',
            'quotation',
            'invoice',
            'commission_date',
            'base_amount',
            'commission_percent',
            'status',
            'notes',
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-control'}),
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'quotation': forms.Select(attrs={'class': 'form-control'}),
            'invoice': forms.Select(attrs={'class': 'form-control'}),
            'commission_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'base_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'commission_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class EmployeePayrollForm(forms.ModelForm):
    class Meta:
        model = EmployeePayroll
        fields = ['employee', 'month', 'year', 'status', 'notes']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-control'}),
            'month': forms.NumberInput(attrs={'class': 'form-control'}),
            'year': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }