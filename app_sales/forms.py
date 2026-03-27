from django import forms

from .models import SalesOrder, SalesOrderItem


class SalesOrderForm(forms.ModelForm):
    class Meta:
        model = SalesOrder
        fields = [
            'customer',
            'quotation',
            'sales_owner',
            'order_date',
            'required_date',
            'payment_terms',
            'delivery_method',
            'internal_delivery_employee',
            'external_courier_name',
            'external_representative_name',
            'external_representative_phone',
            'delivery_address',
            'tracking_number',
            'shipping_fees',
            'notes',
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'quotation': forms.Select(attrs={'class': 'form-control'}),
            'sales_owner': forms.Select(attrs={'class': 'form-control'}),
            'order_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'required_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'payment_terms': forms.Select(attrs={'class': 'form-control'}),
            'delivery_method': forms.Select(attrs={'class': 'form-control'}),
            'internal_delivery_employee': forms.Select(attrs={'class': 'form-control'}),
            'external_courier_name': forms.TextInput(attrs={'class': 'form-control'}),
            'external_representative_name': forms.TextInput(attrs={'class': 'form-control'}),
            'external_representative_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'delivery_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'tracking_number': forms.TextInput(attrs={'class': 'form-control'}),
            'shipping_fees': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        try:
            from app_employees.models import Employee
            sales_qs = Employee.objects.filter(status='Active', can_do_sales=True).order_by('full_name')
            delivery_qs = Employee.objects.filter(status='Active').order_by('full_name')
            self.fields['sales_owner'].queryset = sales_qs
            self.fields['internal_delivery_employee'].queryset = delivery_qs
        except Exception:
            pass


class SalesOrderItemForm(forms.ModelForm):
    class Meta:
        model = SalesOrderItem
        fields = ['item', 'lot', 'description', 'quantity', 'price']
        widgets = {
            'item': forms.Select(attrs={'class': 'form-control'}),
            'lot': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }