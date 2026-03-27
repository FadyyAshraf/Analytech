from django import forms

from .models import (
    MaintenanceRequest,
    PreventiveMaintenancePlan,
    MaintenanceVisit,
)


class MaintenanceRequestForm(forms.ModelForm):
    class Meta:
        model = MaintenanceRequest
        fields = [
            'customer',
            'device',
            'reported_by',
            'contact_phone',
            'issue_description',
            'priority',
            'status',
            'internal_notes',
            'customer_notes',
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'device': forms.Select(attrs={'class': 'form-control'}),
            'reported_by': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'issue_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'internal_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'customer_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class PreventiveMaintenancePlanForm(forms.ModelForm):
    class Meta:
        model = PreventiveMaintenancePlan
        fields = [
            'device',
            'customer',
            'is_active',
            'interval_type',
            'interval_days',
            'start_date',
            'last_visit_date',
            'next_due_date',
            'grace_days',
            'admin_notes',
        ]
        widgets = {
            'device': forms.Select(attrs={'class': 'form-control'}),
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'interval_type': forms.Select(attrs={'class': 'form-control'}),
            'interval_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'last_visit_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'next_due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'grace_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'admin_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class MaintenanceVisitForm(forms.ModelForm):
    class Meta:
        model = MaintenanceVisit
        fields = [
            'request',
            'preventive_plan',
            'customer',
            'device',
            'visit_type',
            'status',
            'visit_date',
            'next_visit_date',
            'engineer',
            'engineer_name',
            'signed_report_received',
            'signed_report_date',
            'device_condition_before',
            'issue_found',
            'work_performed',
            'device_condition_after',
            'final_result',
            'issue_resolved',
            'needs_spare_parts',
            'requires_customer_approval',
            'notes',
        ]
        widgets = {
            'request': forms.Select(attrs={'class': 'form-control'}),
            'preventive_plan': forms.Select(attrs={'class': 'form-control'}),
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'device': forms.Select(attrs={'class': 'form-control'}),
            'visit_type': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'visit_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'next_visit_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'engineer': forms.Select(attrs={'class': 'form-control'}),
            'engineer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'signed_report_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'device_condition_before': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'issue_found': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'work_performed': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'device_condition_after': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'final_result': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        try:
            from app_employees.models import Employee
            self.fields['engineer'].queryset = Employee.objects.filter(
                status='Active',
                can_do_service=True
            ).order_by('full_name')
        except Exception:
            pass