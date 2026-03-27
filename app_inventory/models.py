from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models


class InventoryItem(models.Model):
    ITEM_TYPES = [
        ('Spare Part', 'قطعة غيار'),
        ('Diluent', 'Diluent'),
        ('Lyse', 'Lyse'),
        ('Cleaner', 'Cleaner'),
        ('Control', 'Control'),
        ('Calibrator', 'Calibrator'),
        ('Other', 'أخرى'),
    ]

    item_name = models.CharField(max_length=200, verbose_name='اسم الصنف')
    item_type = models.CharField(max_length=50, choices=ITEM_TYPES, verbose_name='نوع الصنف')
    item_code = models.CharField(max_length=100, unique=True, verbose_name='كود الصنف')
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='إجمالي الكمية')
    unit = models.CharField(max_length=50, blank=True, null=True, verbose_name='الوحدة')
    min_stock = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='الحد الأدنى')
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='سعر الشراء')
    sale_price = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='سعر البيع')
    supplier = models.CharField(max_length=200, blank=True, null=True, verbose_name='المورد')
    notes = models.TextField(blank=True, null=True, verbose_name='ملاحظات')

    class Meta:
        verbose_name = 'صنف مخزني'
        verbose_name_plural = 'أصناف المخزن'
        ordering = ['item_name']

    def is_below_min(self):
        return self.quantity <= self.min_stock

    def __str__(self):
        return f"{self.item_name} ({self.item_code})"


class InventoryLot(models.Model):
    item = models.ForeignKey(
        InventoryItem,
        on_delete=models.CASCADE,
        related_name='lots',
        verbose_name='الصنف'
    )
    lot_number = models.CharField(max_length=100, verbose_name='رقم التشغيلة')
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='كمية التشغيلة')
    expiry_date = models.DateField(blank=True, null=True, verbose_name='تاريخ الانتهاء')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'تشغيلة'
        verbose_name_plural = 'التشغيلات'
        unique_together = ('item', 'lot_number')
        ordering = ['expiry_date', 'created_at', 'id']

    @property
    def available_quantity(self):
        return self.quantity

    def is_expired(self):
        return bool(self.expiry_date and self.expiry_date < date.today())

    def is_expiring_soon(self):
        return bool(self.expiry_date and date.today() <= self.expiry_date <= date.today() + timedelta(days=90))

    def __str__(self):
        return f"{self.item.item_name} - {self.lot_number}"


class RecallNotice(models.Model):
    RISK_LEVELS = [
        ('Low', 'منخفض'),
        ('Medium', 'متوسط'),
        ('High', 'مرتفع'),
        ('Critical', 'حرج'),
    ]

    STATUS_CHOICES = [
        ('Open', 'مفتوح'),
        ('In Progress', 'قيد التنفيذ'),
        ('Closed', 'مغلق'),
    ]

    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, verbose_name='الصنف')
    lot = models.ForeignKey(InventoryLot, on_delete=models.CASCADE, verbose_name='التشغيلة')
    recall_number = models.CharField(max_length=100, unique=True, verbose_name='رقم إشعار السحب')
    notice_date = models.DateField(verbose_name='تاريخ الإشعار')
    reason = models.TextField(verbose_name='سبب السحب')
    risk_level = models.CharField(max_length=20, choices=RISK_LEVELS, verbose_name='درجة الخطورة')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open', verbose_name='الحالة')
    action_required = models.TextField(blank=True, null=True, verbose_name='الإجراء المطلوب')
    notes = models.TextField(blank=True, null=True, verbose_name='ملاحظات')

    class Meta:
        verbose_name = 'إشعار سحب'
        verbose_name_plural = 'إشعارات السحب'
        ordering = ['-notice_date', 'recall_number']

    def __str__(self):
        return f"{self.recall_number} - {self.item.item_name} - {self.lot.lot_number}"


class InventoryTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('IN', 'وارد'),
        ('OUT', 'منصرف'),
        ('ADJUSTMENT', 'تسوية'),
    ]

    SOURCE_TYPES = [
        ('Supplier', 'مورد'),
        ('Customer', 'عميل'),
        ('Customer Return', 'مرتجع عميل'),
        ('Maintenance', 'صيانة'),
        ('Maintenance Return', 'مرتجع صيانة'),
        ('Adjustment', 'تسوية'),
        ('Other', 'أخرى'),
    ]

    item = models.ForeignKey(
        InventoryItem,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name='الصنف'
    )
    lot = models.ForeignKey(
        InventoryLot,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name='التشغيلة'
    )
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES, verbose_name='نوع الحركة')
    source_type = models.CharField(max_length=30, choices=SOURCE_TYPES, blank=True, null=True, verbose_name='مصدر الحركة')
    source_name = models.CharField(max_length=200, blank=True, null=True, verbose_name='اسم المصدر / المرجع')
    quantity = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='الكمية')
    balance_before = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='الرصيد قبل')
    balance_after = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='الرصيد بعد')
    transaction_date = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الحركة')
    reference = models.CharField(max_length=200, blank=True, null=True, verbose_name='المرجع')
    notes = models.TextField(blank=True, null=True, verbose_name='ملاحظات')

    class Meta:
        verbose_name = 'حركة مخزنية'
        verbose_name_plural = 'حركات المخزن'
        ordering = ['transaction_date', 'id']

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError({'quantity': 'الكمية يجب أن تكون أكبر من صفر.'})

        if self.transaction_type == 'IN' and not self.lot:
            raise ValidationError({'lot': 'يجب اختيار التشغيلة في حركة الوارد.'})

        if self.lot and self.lot.item_id != self.item_id:
            raise ValidationError({'lot': 'هذه التشغيلة لا تخص الصنف المختار.'})

        if self.transaction_type == 'OUT' and self.lot:
            recall_exists = RecallNotice.objects.filter(
                lot=self.lot,
                status__in=['Open', 'In Progress']
            ).exists()

            if recall_exists:
                raise ValidationError({
                    'lot': f"لا يمكن الصرف من التشغيلة {self.lot.lot_number} لأنها تحت Recall."
                })

    @staticmethod
    def recalculate_item_transactions(item):
        running_balance = Decimal('0')

        # تصفير كل التشغيلات وإعادة بنائها من الحركات
        for lot in item.lots.all():
            lot.quantity = Decimal('0')
            lot.save(update_fields=['quantity'])

        transactions = item.transactions.all().order_by('transaction_date', 'id')

        for tx in transactions:
            tx.balance_before = running_balance

            if tx.transaction_type == 'IN':
                running_balance += tx.quantity

                if tx.lot:
                    tx.lot.quantity += tx.quantity
                    tx.lot.save(update_fields=['quantity'])

            elif tx.transaction_type == 'OUT':
                qty_to_deduct = tx.quantity

                if qty_to_deduct > running_balance:
                    raise ValidationError(f"لا يوجد رصيد كافي للصنف {item.item_name}")

                if tx.lot:
                    if qty_to_deduct > tx.lot.quantity:
                        raise ValidationError(
                            f"الكمية المطلوبة أكبر من المتاح في التشغيلة {tx.lot.lot_number}"
                        )

                    tx.lot.quantity -= qty_to_deduct
                    tx.lot.save(update_fields=['quantity'])

                else:
                    available_lots = item.lots.filter(quantity__gt=0).order_by('expiry_date', 'created_at', 'id')

                    for lot in available_lots:
                        if qty_to_deduct <= 0:
                            break

                        take_qty = min(qty_to_deduct, lot.quantity)
                        lot.quantity -= take_qty
                        lot.save(update_fields=['quantity'])
                        qty_to_deduct -= take_qty

                    if qty_to_deduct > 0:
                        raise ValidationError(
                            f"لا توجد كميات كافية في التشغيلات المتاحة للصنف {item.item_name}"
                        )

                running_balance -= tx.quantity

            elif tx.transaction_type == 'ADJUSTMENT':
                running_balance = tx.quantity

            tx.balance_after = running_balance
            super(InventoryTransaction, tx).save(
                update_fields=['balance_before', 'balance_after']
            )

        item.quantity = running_balance
        item.save(update_fields=['quantity'])

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        InventoryTransaction.recalculate_item_transactions(self.item)

    def delete(self, *args, **kwargs):
        item = self.item
        super().delete(*args, **kwargs)
        InventoryTransaction.recalculate_item_transactions(item)

    def __str__(self):
        return f"{self.item.item_name} - {self.transaction_type} - {self.quantity}"