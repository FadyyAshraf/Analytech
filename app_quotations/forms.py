from django import forms

from .models import Quotation, QuotationItem


class QuotationForm(forms.ModelForm):
    class Meta:
        model = Quotation
        fields = [
            'customer',
            'customer_name_manual',
            'customer_phone_manual',
            'customer_address_manual',
            'contact_person_manual',
            'device',
            'sales_owner',
            'commission_owner',
            'quotation_type',
            'status',
            'valid_until',
            'reference',
            'subject',
            'maintenance_request',
            'maintenance_visit',
            'discount_percent',
            'vat_percent',
            'notes',
            'terms',
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'customer_name_manual': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_phone_manual': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_address_manual': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'contact_person_manual': forms.TextInput(attrs={'class': 'form-control'}),
            'device': forms.Select(attrs={'class': 'form-control'}),
            'sales_owner': forms.Select(attrs={'class': 'form-control'}),
            'commission_owner': forms.Select(attrs={'class': 'form-control'}),
            'quotation_type': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'valid_until': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'maintenance_request': forms.Select(attrs={'class': 'form-control'}),
            'maintenance_visit': forms.Select(attrs={'class': 'form-control'}),
            'discount_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'vat_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'terms': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        try:
            from app_employees.models import Employee
            sales_qs = Employee.objects.filter(status='Active', can_do_sales=True).order_by('full_name')
            self.fields['sales_owner'].queryset = sales_qs
            self.fields['commission_owner'].queryset = sales_qs
        except Exception:
            pass


class QuotationItemForm(forms.ModelForm):
    class Meta:
        model = QuotationItem
        fields = [
            'item_type',
            'inventory_item',
            'maintenance_requirement',
            'description',
            'quantity',
            'price',
        ]
        widgets = {
            'item_type': forms.Select(attrs={'class': 'form-control'}),
            'inventory_item': forms.Select(attrs={'class': 'form-control'}),
            'maintenance_requirement': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }