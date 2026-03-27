from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import models, transaction

from accounting.models import JournalEntry, JournalEntryLine, Account
from app_inventory.models import InventoryItem, InventoryLot, InventoryTransaction
from app_quotations.models import Quotation


TWO_PLACES = Decimal('0.01')


class Invoice(models.Model):
    STATUS_CHOICES = [
        ('draft', 'مسودة'),
        ('posted', 'مرحلة'),
        ('cancelled', 'ملغاة'),
    ]

    quotation = models.OneToOneField(
        Quotation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoice',
        verbose_name='عرض السعر'
    )

    customer_name = models.CharField(max_length=200, verbose_name='اسم العميل')
    invoice_date = models.DateField(auto_now_add=True, verbose_name='تاريخ الفاتورة')

    sales_owner = models.ForeignKey(
        'app_employees.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sales_invoices',
        verbose_name='الموظف المسؤول عن البيع'
    )

    commission_owner = models.ForeignKey(
        'app_employees.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='commission_invoices',
        verbose_name='صاحب العمولة'
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='الحالة')
    stock_posted = models.BooleanField(default=False, verbose_name='تم ترحيل المخزن')

    journal_entry = models.OneToOneField(
        JournalEntry,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoice',
        verbose_name='القيد المحاسبي'
    )

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='الإجمالي قبل الخصم')
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='نسبة الخصم %')
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='قيمة الخصم')
    net_before_vat = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='الصافي قبل الضريبة')
    vat_percent = models.DecimalField(max_digits=5, decimal_places=2, default=14, verbose_name='نسبة الضريبة %')
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='قيمة الضريبة')
    total_after_vat = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='الإجمالي النهائي')

    notes = models.TextField(blank=True, null=True, verbose_name='ملاحظات')

    class Meta:
        verbose_name = 'فاتورة'
        verbose_name_plural = 'الفواتير'
        ordering = ['-id']

    def __str__(self):
        return f"فاتورة {self.id} - {self.customer_name}"

    def recalculate_totals(self):
        subtotal = sum((item.total for item in self.items.all()), Decimal('0'))
        subtotal = subtotal.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

        discount_amount = (subtotal * (self.discount_percent / Decimal('100'))).quantize(
            TWO_PLACES, rounding=ROUND_HALF_UP
        )
        net_before_vat = (subtotal - discount_amount).quantize(
            TWO_PLACES, rounding=ROUND_HALF_UP
        )
        vat_amount = (net_before_vat * (self.vat_percent / Decimal('100'))).quantize(
            TWO_PLACES, rounding=ROUND_HALF_UP
        )
        total_after_vat = (net_before_vat + vat_amount).quantize(
            TWO_PLACES, rounding=ROUND_HALF_UP
        )

        Invoice.objects.filter(pk=self.pk).update(
            subtotal=subtotal,
            discount_amount=discount_amount,
            net_before_vat=net_before_vat,
            vat_amount=vat_amount,
            total_after_vat=total_after_vat,
        )

        self.subtotal = subtotal
        self.discount_amount = discount_amount
        self.net_before_vat = net_before_vat
        self.vat_amount = vat_amount
        self.total_after_vat = total_after_vat

    def get_customer_account(self):
        if self.quotation and self.quotation.customer:
            customer = self.quotation.customer
            if not customer.account_id:
                customer.create_account_if_missing()
                customer.refresh_from_db()
            if customer.account_id:
                return customer.account
        return Account.objects.get(code='1100')

    def create_journal_entry(self):
        if self.journal_entry:
            return

        customers_account = self.get_customer_account()
        sales_account = Account.objects.get(code='4100')
        vat_account = Account.objects.get(code='2100')

        entry = JournalEntry.objects.create(
            entry_date=self.invoice_date,
            description=f'فاتورة رقم {self.id} - {self.customer_name}',
            reference=f'INV-{self.id}',
            source_type='Invoice',
            source_id=self.id,
            status='Draft'
        )

        JournalEntryLine.objects.create(
            entry=entry,
            account=customers_account,
            description=f'إثبات مديونية العميل - فاتورة {self.id}',
            debit=self.total_after_vat,
            credit=0
        )

        JournalEntryLine.objects.create(
            entry=entry,
            account=sales_account,
            description=f'إيراد مبيعات - فاتورة {self.id}',
            debit=0,
            credit=self.net_before_vat
        )

        if self.vat_amount > 0:
            JournalEntryLine.objects.create(
                entry=entry,
                account=vat_account,
                description=f'ضريبة قيمة مضافة - فاتورة {self.id}',
                debit=0,
                credit=self.vat_amount
            )

        entry.post()
        self.journal_entry = entry
        self.save(update_fields=['journal_entry'])

    def create_employee_commission(self):
        if not self.commission_owner:
            return

        if self.employee_commissions.filter(employee=self.commission_owner).exists():
            return

        from app_employees.models import EmployeeCommission

        commission_percent = self.commission_owner.sales_commission_percent or Decimal('0')

        if commission_percent <= 0:
            return

        EmployeeCommission.objects.create(
            employee=self.commission_owner,
            customer=self.quotation.customer if self.quotation and self.quotation.customer else None,
            quotation=self.quotation if self.quotation_id else None,
            invoice=self,
            commission_date=self.invoice_date,
            base_amount=self.total_after_vat,
            commission_percent=commission_percent,
            status='Approved',
            notes=f'عمولة تلقائية من الفاتورة رقم {self.id}'
        )

    @transaction.atomic
    def post_invoice(self):
        if self.status == 'posted' or self.stock_posted:
            raise ValidationError('تم ترحيل هذه الفاتورة مسبقًا.')

        items = self.items.select_related('item', 'lot').all()
        if not items.exists():
            raise ValidationError('لا يمكن ترحيل فاتورة بدون أصناف.')

        for item in items:
            if not item.item:
                raise ValidationError('يوجد بند في الفاتورة بدون صنف مخزني.')

            if not item.lot:
                item.assign_default_lot(save_item=False)

            if not item.lot:
                raise ValidationError(f'لا توجد تشغيلة متاحة للبند: {item.item}')

            if item.lot.item_id != item.item_id:
                raise ValidationError(f'التشغيلة لا تخص الصنف: {item.item}')

            if item.quantity > item.lot.available_quantity:
                raise ValidationError(f'الكمية المطلوبة من {item.item} أكبر من المتاح في التشغيلة.')

        for item in items:
            InventoryTransaction.objects.create(
                item=item.item,
                lot=item.lot,
                transaction_type='OUT',
                quantity=item.quantity,
                source_type='Customer',
                source_name=f"فاتورة رقم {self.id}",
                reference=f"INV-{self.id}",
                notes='صرف تلقائي عند ترحيل الفاتورة'
            )

        self.create_journal_entry()
        self.create_employee_commission()

        self.status = 'posted'
        self.stock_posted = True
        self.save(update_fields=['status', 'stock_posted'])

    @transaction.atomic
    def cancel_invoice(self):
        if self.status == 'cancelled':
            raise ValidationError('هذه الفاتورة ملغاة بالفعل.')

        if self.status == 'posted' and self.stock_posted:
            for item in self.items.select_related('item', 'lot').all():
                if item.item and item.lot:
                    InventoryTransaction.objects.create(
                        item=item.item,
                        lot=item.lot,
                        transaction_type='IN',
                        quantity=item.quantity,
                        source_type='Customer Return',
                        source_name=f"إلغاء فاتورة رقم {self.id}",
                        reference=f"INV-{self.id}",
                        notes='رد تلقائي نتيجة إلغاء الفاتورة'
                    )

        if self.journal_entry:
            self.journal_entry.cancel()

        self.employee_commissions.update(status='Cancelled')

        self.status = 'cancelled'
        self.stock_posted = False
        self.save(update_fields=['status', 'stock_posted'])


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='الفاتورة'
    )
    item = models.ForeignKey(
        InventoryItem,
        on_delete=models.PROTECT,
        verbose_name='الصنف'
    )
    lot = models.ForeignKey(
        InventoryLot,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='التشغيلة'
    )
    description = models.CharField(max_length=255, blank=True, null=True, verbose_name='وصف البند')
    quantity = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='الكمية')
    price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='سعر الوحدة')
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='إجمالي البند')

    class Meta:
        verbose_name = 'بند فاتورة'
        verbose_name_plural = 'بنود الفاتورة'

    def __str__(self):
        return f"{self.item} - {self.quantity}"

    def assign_default_lot(self, save_item=False):
        if self.item and not self.lot:
            default_lot = InventoryLot.objects.filter(item=self.item).order_by('id').first()
            if default_lot:
                self.lot = default_lot
                if save_item and self.pk:
                    self.save(update_fields=['lot'])

    def clean(self):
        if self.quantity is None or self.quantity <= 0:
            raise ValidationError({'quantity': 'الكمية يجب أن تكون أكبر من صفر.'})
        if not self.item:
            raise ValidationError({'item': 'يجب اختيار الصنف.'})
        if self.lot and self.lot.item_id != self.item_id:
            raise ValidationError({'lot': 'هذه التشغيلة لا تخص الصنف المختار.'})

        invoice_obj = getattr(self, 'invoice', None)
        if invoice_obj is not None:
            if invoice_obj.status == 'posted':
                raise ValidationError('لا يمكن تعديل بنود فاتورة تم ترحيلها.')
            if invoice_obj.status == 'cancelled':
                raise ValidationError('لا يمكن تعديل بنود فاتورة ملغاة.')

    def save(self, *args, **kwargs):
        if not self.description and self.item:
            self.description = self.item.item_name
        if not self.lot and self.item:
            self.assign_default_lot(save_item=False)

        self.total = (self.quantity * self.price).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        self.full_clean()
        super().save(*args, **kwargs)

        if self.invoice_id:
            self.invoice.recalculate_totals()

    def delete(self, *args, **kwargs):
        invoice_obj = getattr(self, 'invoice', None)

        if invoice_obj is not None:
            if invoice_obj.status == 'posted':
                raise ValidationError('لا يمكن حذف بند من فاتورة تم ترحيلها.')
            if invoice_obj.status == 'cancelled':
                raise ValidationError('لا يمكن حذف بند من فاتورة ملغاة.')

        super().delete(*args, **kwargs)

        if invoice_obj is not None:
            invoice_obj.recalculate_totals()


class InvoicePrintSettings(models.Model):
    company_name = models.CharField(max_length=200, default='Analytech', verbose_name='اسم الشركة')
    company_subtitle = models.CharField(max_length=300, blank=True, null=True, verbose_name='وصف الشركة')
    footer_text_ar = models.TextField(blank=True, null=True, verbose_name='نص الفوتر عربي')
    footer_text_en = models.TextField(blank=True, null=True, verbose_name='نص الفوتر English')
    logo = models.ImageField(upload_to='invoice_assets/', blank=True, null=True, verbose_name='صورة الهيدر')

    class Meta:
        verbose_name = 'إعدادات طباعة الفواتير'
        verbose_name_plural = 'إعدادات طباعة الفواتير'

    def __str__(self):
        return self.company_name