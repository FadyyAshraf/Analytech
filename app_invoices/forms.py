from django import forms
from .models import Invoice, InvoiceItem


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = [
            'customer_name',
            'sales_owner',
            'commission_owner',
            'discount_percent',
            'vat_percent',
            'notes',
        ]
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'sales_owner': forms.Select(attrs={'class': 'form-control'}),
            'commission_owner': forms.Select(attrs={'class': 'form-control'}),
            'discount_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'vat_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
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


class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ['item', 'lot', 'description', 'quantity', 'price']
        widgets = {
            'item': forms.Select(attrs={'class': 'form-control item-select'}),
            'lot': forms.Select(attrs={'class': 'form-control lot-select'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control qty-input', 'step': '0.01'}),
            'price': forms.NumberInput(attrs={'class': 'form-control price-input', 'step': '0.01'}),
        }