from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

TWO_PLACES = Decimal('0.01')


class SalesOrder(models.Model):
    STATUS_CHOICES = [
        ('Draft', 'مسودة'),
        ('Confirmed', 'معتمد'),
        ('Ready', 'جاهز للصرف'),
        ('Partially Released', 'صرف جزئي'),
        ('Released', 'تم الصرف'),
        ('Shipped', 'تم الشحن'),
        ('Delivered', 'تم التسليم'),
        ('Closed', 'مغلق'),
        ('Cancelled', 'ملغي'),
    ]

    PAYMENT_TERMS_CHOICES = [
        ('Cash Before Delivery', 'نقدي قبل التسليم'),
        ('Cash On Delivery', 'نقدي عند التسليم'),
        ('Credit', 'آجل'),
        ('Bank Transfer', 'تحويل بنكي'),
        ('Mixed', 'مختلط'),
    ]

    DELIVERY_METHOD_CHOICES = [
        ('Internal Employee', 'مندوب من موظفي الشركة'),
        ('External Courier', 'شركة شحن'),
        ('External Representative', 'مندوب خارجي'),
        ('Customer Pickup', 'استلام من العميل'),
    ]

    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.CASCADE,
        related_name='sales_orders',
        verbose_name='العميل'
    )

    quotation = models.ForeignKey(
        'app_quotations.Quotation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sales_orders',
        verbose_name='عرض السعر'
    )

    invoice = models.ForeignKey(
        'app_invoices.Invoice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sales_orders',
        verbose_name='الفاتورة'
    )

    sales_owner = models.ForeignKey(
        'app_employees.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sales_orders',
        verbose_name='الموظف المسؤول عن الطلب'
    )

    order_date = models.DateField(default=timezone.localdate, verbose_name='تاريخ الطلب')
    required_date = models.DateField(null=True, blank=True, verbose_name='التاريخ المطلوب')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Draft', verbose_name='الحالة')

    payment_terms = models.CharField(
        max_length=30,
        choices=PAYMENT_TERMS_CHOICES,
        default='Credit',
        verbose_name='شروط السداد'
    )

    delivery_method = models.CharField(
        max_length=30,
        choices=DELIVERY_METHOD_CHOICES,
        default='Internal Employee',
        verbose_name='طريقة التوصيل'
    )

    internal_delivery_employee = models.ForeignKey(
        'app_employees.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='delivery_orders',
        verbose_name='مندوب التوصيل الداخلي'
    )

    external_courier_name = models.CharField(max_length=200, blank=True, null=True, verbose_name='اسم شركة الشحن')
    external_representative_name = models.CharField(max_length=200, blank=True, null=True, verbose_name='اسم المندوب الخارجي')
    external_representative_phone = models.CharField(max_length=50, blank=True, null=True, verbose_name='هاتف المندوب الخارجي')

    delivery_address = models.TextField(blank=True, null=True, verbose_name='عنوان التوصيل')
    tracking_number = models.CharField(max_length=100, blank=True, null=True, verbose_name='رقم الشحنة / التتبع')
    shipping_fees = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='رسوم الشحن')

    released_at = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ الصرف من المخزن')
    shipped_at = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ الشحن / الخروج')
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ التسليم')
    customer_confirmed_receipt = models.BooleanField(default=False, verbose_name='تم تأكيد استلام العميل')
    customer_confirmed_at = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ تأكيد الاستلام')

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='الإجمالي')
    notes = models.TextField(blank=True, null=True, verbose_name='ملاحظات')

    class Meta:
        verbose_name = 'طلب بيع'
        verbose_name_plural = 'طلبات البيع'
        ordering = ['-id']

    def __str__(self):
        return f'طلب بيع {self.id} - {self.customer.name}'

    def clean(self):
        if self.delivery_method == 'Internal Employee' and not self.internal_delivery_employee:
            raise ValidationError('يجب اختيار مندوب داخلي عند اختيار التوصيل بواسطة موظف من الشركة.')

        if self.delivery_method == 'External Courier' and not self.external_courier_name:
            raise ValidationError('يجب كتابة اسم شركة الشحن.')

        if self.delivery_method == 'External Representative' and not self.external_representative_name:
            raise ValidationError('يجب كتابة اسم المندوب الخارجي.')

    def recalculate_totals(self):
        subtotal = sum((item.total for item in self.items.all()), Decimal('0'))
        subtotal = subtotal.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

        SalesOrder.objects.filter(pk=self.pk).update(subtotal=subtotal)
        self.subtotal = subtotal

    def mark_confirmed(self):
        if self.status != 'Draft':
            raise ValidationError('يمكن اعتماد الطلب فقط من حالة مسودة.')
        self.status = 'Confirmed'
        self.save(update_fields=['status'])

    @transaction.atomic
    def release_from_inventory(self):
        if self.status not in ['Confirmed', 'Ready', 'Partially Released']:
            raise ValidationError('لا يمكن صرف الطلب من المخزن في حالته الحالية.')

        from app_inventory.models import InventoryTransaction, InventoryLot

        if not self.items.exists():
            raise ValidationError('لا يمكن صرف طلب بدون بنود.')

        released_any = False

        for item in self.items.select_related('item', 'lot').all():
            if item.qty_released >= item.quantity:
                continue

            remaining = item.quantity - item.qty_released

            lot = item.lot
            if not lot:
                lot = InventoryLot.objects.filter(item=item.item).order_by('id').first()
                if lot:
                    item.lot = lot
                    item.save(update_fields=['lot'])

            if not lot:
                continue

            available = lot.available_quantity
            if available <= 0:
                continue

            qty_to_release = remaining if available >= remaining else available

            InventoryTransaction.objects.create(
                item=item.item,
                lot=lot,
                transaction_type='OUT',
                quantity=qty_to_release,
                source_type='Customer',
                source_name=f'Sales Order {self.id}',
                reference=f'SO-{self.id}',
                notes='صرف تلقائي من طلب البيع'
            )

            item.qty_released += qty_to_release
            item.save(update_fields=['qty_released'])
            released_any = True

        if not released_any:
            raise ValidationError('لم يتم صرف أي كميات من المخزن.')

        if any(x.qty_released < x.quantity for x in self.items.all()):
            self.status = 'Partially Released'
        else:
            self.status = 'Released'

        self.released_at = timezone.now()
        self.save(update_fields=['status', 'released_at'])

    def mark_shipped(self):
        if self.status not in ['Released', 'Partially Released']:
            raise ValidationError('لا يمكن شحن الطلب قبل الصرف من المخزن.')
        self.status = 'Shipped'
        self.shipped_at = timezone.now()
        self.save(update_fields=['status', 'shipped_at'])

    def mark_delivered(self):
        if self.status not in ['Shipped', 'Released', 'Partially Released']:
            raise ValidationError('لا يمكن تأكيد التسليم قبل الشحن أو الصرف.')
        self.status = 'Delivered'
        self.delivered_at = timezone.now()
        self.customer_confirmed_receipt = True
        self.customer_confirmed_at = timezone.now()
        self.save(update_fields=[
            'status',
            'delivered_at',
            'customer_confirmed_receipt',
            'customer_confirmed_at'
        ])

    def close_order(self):
        if self.status not in ['Delivered', 'Released', 'Partially Released', 'Shipped']:
            raise ValidationError('لا يمكن إغلاق الطلب في حالته الحالية.')
        self.status = 'Closed'
        self.save(update_fields=['status'])


class SalesOrderItem(models.Model):
    order = models.ForeignKey(
        SalesOrder,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='طلب البيع'
    )

    item = models.ForeignKey(
        'app_inventory.InventoryItem',
        on_delete=models.PROTECT,
        related_name='sales_order_items',
        verbose_name='الصنف'
    )

    lot = models.ForeignKey(
        'app_inventory.InventoryLot',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sales_order_items',
        verbose_name='التشغيلة'
    )

    description = models.CharField(max_length=255, blank=True, null=True, verbose_name='الوصف')
    quantity = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='الكمية المطلوبة')
    qty_released = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='الكمية المنصرفة')
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='سعر الوحدة')
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='الإجمالي')

    class Meta:
        verbose_name = 'بند طلب بيع'
        verbose_name_plural = 'بنود طلبات البيع'

    def __str__(self):
        return f'{self.item.item_name} - {self.quantity}'

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError('الكمية يجب أن تكون أكبر من صفر.')
        if self.lot and self.lot.item_id != self.item_id:
            raise ValidationError('التشغيلة المختارة لا تخص هذا الصنف.')

    def save(self, *args, **kwargs):
        if not self.description and self.item_id:
            self.description = self.item.item_name

        self.total = (self.quantity * self.price).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        self.full_clean()
        super().save(*args, **kwargs)

        if self.order_id:
            self.order.recalculate_totals()

    def delete(self, *args, **kwargs):
        order = self.order
        super().delete(*args, **kwargs)
        order.recalculate_totals()