from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone


class Account(models.Model):
    ACCOUNT_TYPES = [
        ('Asset', 'أصل'),
        ('Liability', 'التزام'),
        ('Equity', 'حقوق ملكية'),
        ('Revenue', 'إيراد'),
        ('Expense', 'مصروف'),
    ]

    name = models.CharField(max_length=200, verbose_name='اسم الحساب')
    code = models.CharField(max_length=50, unique=True, verbose_name='كود الحساب')
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, verbose_name='نوع الحساب')
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='الحساب الأب'
    )
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    notes = models.TextField(blank=True, null=True, verbose_name='ملاحظات')

    class Meta:
        verbose_name = 'حساب'
        verbose_name_plural = 'شجرة الحسابات'
        ordering = ['code', 'name']

    def __str__(self):
        return f'{self.code} - {self.name}'

    @property
    def current_debit(self):
        return sum(
            (line.debit for line in self.entry_lines.filter(entry__status='Posted')),
            Decimal('0')
        )

    @property
    def current_credit(self):
        return sum(
            (line.credit for line in self.entry_lines.filter(entry__status='Posted')),
            Decimal('0')
        )

    @property
    def current_balance(self):
        return self.current_debit - self.current_credit

    @property
    def movement_count(self):
        return self.entry_lines.filter(entry__status='Posted').count()


class JournalEntry(models.Model):
    ENTRY_STATUS = [
        ('Draft', 'مسودة'),
        ('Posted', 'مرحّل'),
        ('Cancelled', 'ملغي'),
    ]

    entry_date = models.DateField(default=timezone.localdate, verbose_name='تاريخ القيد')
    description = models.CharField(max_length=255, verbose_name='البيان')
    reference = models.CharField(max_length=100, blank=True, null=True, verbose_name='المرجع')
    status = models.CharField(max_length=20, choices=ENTRY_STATUS, default='Draft', verbose_name='الحالة')

    source_type = models.CharField(max_length=50, blank=True, null=True, verbose_name='نوع المصدر')
    source_id = models.PositiveIntegerField(blank=True, null=True, verbose_name='رقم المصدر')

    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True, verbose_name='ملاحظات')

    class Meta:
        verbose_name = 'قيد يومية'
        verbose_name_plural = 'القيود اليومية'
        ordering = ['-entry_date', '-id']

    def __str__(self):
        return f'قيد {self.id} - {self.entry_date}'

    @property
    def total_debit(self):
        return sum((line.debit for line in self.lines.all()), Decimal('0'))

    @property
    def total_credit(self):
        return sum((line.credit for line in self.lines.all()), Decimal('0'))

    def clean(self):
        if self.status == 'Posted' and self.total_debit != self.total_credit:
            raise ValidationError('لا يمكن ترحيل قيد غير متوازن.')

    def post(self):
        if self.status == 'Posted':
            raise ValidationError('تم ترحيل هذا القيد بالفعل.')

        if not self.lines.exists():
            raise ValidationError('لا يمكن ترحيل قيد بدون سطور.')

        if self.total_debit != self.total_credit:
            raise ValidationError('القيد غير متوازن. يجب أن يتساوى المدين مع الدائن.')

        self.status = 'Posted'
        self.save(update_fields=['status'])

    def cancel(self):
        if self.status == 'Cancelled':
            raise ValidationError('هذا القيد ملغي بالفعل.')

        self.status = 'Cancelled'
        self.save(update_fields=['status'])


class JournalEntryLine(models.Model):
    entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name='القيد'
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='entry_lines',
        verbose_name='الحساب'
    )
    description = models.CharField(max_length=255, blank=True, null=True, verbose_name='بيان السطر')
    debit = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name='مدين')
    credit = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name='دائن')

    class Meta:
        verbose_name = 'سطر قيد'
        verbose_name_plural = 'سطور القيود'

    def __str__(self):
        return f'{self.account.name}'

    def clean(self):
        if self.debit < 0 or self.credit < 0:
            raise ValidationError('لا يجوز أن تكون القيم سالبة.')

        if self.debit == 0 and self.credit == 0:
            raise ValidationError('يجب إدخال قيمة مدين أو دائن.')

        if self.debit > 0 and self.credit > 0:
            raise ValidationError('لا يجوز إدخال مدين ودائن في نفس السطر.')

        if self.entry.status == 'Posted':
            raise ValidationError('لا يمكن تعديل سطور قيد تم ترحيله.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class ReceiptVoucher(models.Model):
    PAYMENT_METHODS = [
        ('Cash', 'نقدي'),
        ('Bank', 'بنك'),
        ('Cheque', 'شيك'),
        ('Transfer', 'تحويل'),
        ('Other', 'أخرى'),
    ]

    voucher_date = models.DateField(default=timezone.localdate, verbose_name='التاريخ')
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='receipt_vouchers',
        verbose_name='العميل'
    )
    payer_name = models.CharField(max_length=200, verbose_name='اسم الدافع')
    amount = models.DecimalField(max_digits=14, decimal_places=2, verbose_name='المبلغ')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='Cash', verbose_name='طريقة السداد')
    reference = models.CharField(max_length=100, blank=True, null=True, verbose_name='المرجع')
    description = models.CharField(max_length=255, verbose_name='البيان')

    debit_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='receipt_debit_vouchers',
        verbose_name='الحساب المدين'
    )
    credit_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='receipt_credit_vouchers',
        verbose_name='الحساب الدائن'
    )

    journal_entry = models.OneToOneField(
        JournalEntry,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='receipt_voucher',
        verbose_name='القيد المرتبط'
    )

    notes = models.TextField(blank=True, null=True, verbose_name='ملاحظات')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'سند قبض'
        verbose_name_plural = 'سندات القبض'
        ordering = ['-voucher_date', '-id']

    def __str__(self):
        return f'سند قبض {self.id} - {self.payer_name}'

    def clean(self):
        if self.amount <= 0:
            raise ValidationError('المبلغ يجب أن يكون أكبر من صفر.')

    def save(self, *args, **kwargs):
        if self.customer and not self.payer_name:
            self.payer_name = self.customer.name

        if self.customer:
            if not self.customer.account_id:
                self.customer.create_account_if_missing()
                self.customer.refresh_from_db()

            self.credit_account = self.customer.account

        super().save(*args, **kwargs)

    @transaction.atomic
    def create_journal_entry(self):
        if self.journal_entry:
            raise ValidationError('تم إنشاء قيد لهذا السند بالفعل.')

        entry = JournalEntry.objects.create(
            entry_date=self.voucher_date,
            description=f'سند قبض رقم {self.id} - {self.description}',
            reference=self.reference,
            source_type='ReceiptVoucher',
            source_id=self.id,
            status='Draft',
            notes=self.notes
        )

        JournalEntryLine.objects.create(
            entry=entry,
            account=self.debit_account,
            description=self.description,
            debit=self.amount,
            credit=0
        )

        JournalEntryLine.objects.create(
            entry=entry,
            account=self.credit_account,
            description=self.description,
            debit=0,
            credit=self.amount
        )

        entry.post()
        self.journal_entry = entry
        self.save(update_fields=['journal_entry'])


class PaymentVoucher(models.Model):
    PAYMENT_METHODS = [
        ('Cash', 'نقدي'),
        ('Bank', 'بنك'),
        ('Cheque', 'شيك'),
        ('Transfer', 'تحويل'),
        ('Other', 'أخرى'),
    ]

    voucher_date = models.DateField(default=timezone.localdate, verbose_name='التاريخ')
    payee_name = models.CharField(max_length=200, verbose_name='اسم المستفيد')
    amount = models.DecimalField(max_digits=14, decimal_places=2, verbose_name='المبلغ')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='Cash', verbose_name='طريقة السداد')
    reference = models.CharField(max_length=100, blank=True, null=True, verbose_name='المرجع')
    description = models.CharField(max_length=255, verbose_name='البيان')

    debit_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='payment_debit_vouchers',
        verbose_name='الحساب المدين'
    )
    credit_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='payment_credit_vouchers',
        verbose_name='الحساب الدائن'
    )

    journal_entry = models.OneToOneField(
        JournalEntry,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payment_voucher',
        verbose_name='القيد المرتبط'
    )

    notes = models.TextField(blank=True, null=True, verbose_name='ملاحظات')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'سند صرف'
        verbose_name_plural = 'سندات الصرف'
        ordering = ['-voucher_date', '-id']

    def __str__(self):
        return f'سند صرف {self.id} - {self.payee_name}'

    @transaction.atomic
    def create_journal_entry(self):
        if self.journal_entry:
            raise ValidationError('تم إنشاء قيد لهذا السند بالفعل.')

        entry = JournalEntry.objects.create(
            entry_date=self.voucher_date,
            description=f'سند صرف رقم {self.id} - {self.description}',
            reference=self.reference,
            source_type='PaymentVoucher',
            source_id=self.id,
            status='Draft',
            notes=self.notes
        )

        JournalEntryLine.objects.create(
            entry=entry,
            account=self.debit_account,
            description=self.description,
            debit=self.amount,
            credit=0
        )

        JournalEntryLine.objects.create(
            entry=entry,
            account=self.credit_account,
            description=self.description,
            debit=0,
            credit=self.amount
        )

        entry.post()
        self.journal_entry = entry
        self.save(update_fields=['journal_entry'])