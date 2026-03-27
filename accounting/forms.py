from django import forms
from django.core.exceptions import ValidationError

from .models import (
    Account,
    JournalEntry,
    JournalEntryLine,
    ReceiptVoucher,
    PaymentVoucher,
)


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['code', 'name', 'account_type', 'parent', 'is_active', 'notes']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'account_type': forms.Select(attrs={'class': 'form-control'}),
            'parent': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class JournalEntryForm(forms.ModelForm):
    class Meta:
        model = JournalEntry
        fields = ['entry_date', 'description', 'reference', 'status', 'notes']
        widgets = {
            'entry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class JournalEntryLineForm(forms.ModelForm):
    class Meta:
        model = JournalEntryLine
        fields = ['account', 'description', 'debit', 'credit']
        widgets = {
            'account': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'debit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'credit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class ReceiptVoucherForm(forms.ModelForm):
    class Meta:
        model = ReceiptVoucher
        fields = [
            'voucher_date',
            'customer',
            'payer_name',
            'amount',
            'payment_method',
            'reference',
            'description',
            'debit_account',
            'credit_account',
            'notes',
        ]
        widgets = {
            'voucher_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'payer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'debit_account': forms.Select(attrs={'class': 'form-control'}),
            'credit_account': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # حسابات التحصيل فقط: أصول نشطة وغير مربوطة بعملاء
        self.fields['debit_account'].queryset = Account.objects.filter(
            account_type='Asset',
            is_active=True,
            customer__isnull=True
        ).order_by('code')

        # الحساب الدائن يحدد تلقائيًا من العميل
        self.fields['credit_account'].queryset = Account.objects.filter(
            account_type='Asset',
            is_active=True
        ).order_by('code')

        self.fields['credit_account'].required = False
        self.fields['credit_account'].label = 'حساب العميل (يتحدد تلقائيًا)'
        self.fields['debit_account'].label = 'حساب التحصيل (الخزينة / البنك)'

        if self.fields['debit_account'].queryset.count() == 0:
            self.fields['debit_account'].help_text = (
                'لا توجد حسابات تحصيل متاحة. أضف أولًا حساب أصل غير مربوط بعميل مثل 1000 الخزينة أو 1010 البنك.'
            )

    def clean(self):
        cleaned_data = super().clean()

        customer = cleaned_data.get('customer')
        debit_account = cleaned_data.get('debit_account')

        if not debit_account:
            raise ValidationError('يجب اختيار حساب التحصيل (الخزينة أو البنك).')

        if customer:
            if not customer.account_id:
                customer.create_account_if_missing()
                customer.refresh_from_db()

            customer_account = customer.account
            cleaned_data['credit_account'] = customer_account

            if debit_account and customer_account and debit_account.id == customer_account.id:
                raise ValidationError('لا يجوز أن يكون حساب التحصيل هو نفس حساب العميل في سند القبض.')

        credit_account = cleaned_data.get('credit_account')
        if debit_account and credit_account and debit_account.id == credit_account.id:
            raise ValidationError('لا يجوز أن يكون الحساب المدين هو نفس الحساب الدائن.')

        return cleaned_data


class PaymentVoucherForm(forms.ModelForm):
    class Meta:
        model = PaymentVoucher
        fields = [
            'voucher_date',
            'payee_name',
            'amount',
            'payment_method',
            'reference',
            'description',
            'debit_account',
            'credit_account',
            'notes',
        ]
        widgets = {
            'voucher_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'payee_name': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'debit_account': forms.Select(attrs={'class': 'form-control'}),
            'credit_account': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        debit_account = cleaned_data.get('debit_account')
        credit_account = cleaned_data.get('credit_account')

        if debit_account and credit_account and debit_account.id == credit_account.id:
            raise ValidationError('لا يجوز أن يكون الحساب المدين هو نفس الحساب الدائن.')

        return cleaned_data