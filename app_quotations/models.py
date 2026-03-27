from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models

from customers.models import Customer
from app_devices.models import Device


class Quotation(models.Model):
    QUOTATION_TYPES = [
        ('Devices', 'أجهزة'),
        ('Consumables', 'محاليل ومستلزمات'),
        ('Spare Parts', 'قطع غيار'),
        ('Service', 'خدمة / صيانة'),
        ('Mixed', 'مختلط'),
        ('Other', 'أخرى'),
    ]

    STATUS_CHOICES = [
        ('Draft', 'مسودة'),
        ('Sent', 'تم الإرسال'),
        ('Approved', 'تمت الموافقة'),
        ('Rejected', 'مرفوض'),
        ('Expired', 'منتهي'),
        ('Converted', 'تم التحويل إلى فاتورة'),
    ]

    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quotations',
        verbose_name='العميل المسجل'
    )

    customer_name_manual = models.CharField(max_length=200, blank=True, null=True, verbose_name='اسم العميل اليدوي')
    customer_phone_manual = models.CharField(max_length=50, blank=True, null=True, verbose_name='هاتف العميل اليدوي')
    customer_address_manual = models.TextField(blank=True, null=True, verbose_name='عنوان العميل اليدوي')
    contact_person_manual = models.CharField(max_length=150, blank=True, null=True, verbose_name='الشخص المسؤول يدويًا')

    device = models.ForeignKey(
        Device,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quotations',
        verbose_name='الجهاز المرجعي'
    )

    sales_owner = models.ForeignKey(
        'app_employees.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sales_quotations',
        verbose_name='الموظف المسؤول عن البيع'
    )

    commission_owner = models.ForeignKey(
        'app_employees.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='commission_quotations',
        verbose_name='صاحب العمولة'
    )

    quotation_type = models.CharField(max_length=30, choices=QUOTATION_TYPES, default='Mixed', verbose_name='نوع عرض السعر')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft', verbose_name='الحالة')

    quotation_date = models.DateField(auto_now_add=True, verbose_name='تاريخ العرض')
    valid_until = models.DateField(null=True, blank=True, verbose_name='ساري حتى')

    reference = models.CharField(max_length=200, blank=True, null=True, verbose_name='مرجع')
    subject = models.CharField(max_length=255, verbose_name='موضوع العرض')

    maintenance_request = models.ForeignKey(
        'app_maintenance.MaintenanceRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quotations',
        verbose_name='طلب الصيانة المرتبط'
    )
    maintenance_visit = models.ForeignKey(
        'app_maintenance.MaintenanceVisit',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quotations',
        verbose_name='زيارة الصيانة المرتبطة'
    )

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='الإجمالي قبل الخصم')
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='نسبة الخصم %')
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='قيمة الخصم')
    net_before_vat = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='الصافي قبل الضريبة')
    vat_percent = models.DecimalField(max_digits=5, decimal_places=2, default=14, verbose_name='نسبة الضريبة %')
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='قيمة الضريبة')
    total_after_vat = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='الإجمالي النهائي')

    notes = models.TextField(blank=True, null=True, verbose_name='ملاحظات')
    terms = models.TextField(blank=True, null=True, verbose_name='الشروط والأحكام')

    class Meta:
        verbose_name = 'عرض سعر'
        verbose_name_plural = 'عروض الأسعار'
        ordering = ['-id']

    def clean(self):
        if not self.customer and not self.customer_name_manual:
            raise ValidationError('يجب اختيار عميل مسجل أو كتابة اسم عميل يدوي.')

    @property
    def display_customer_name(self):
        if self.customer:
            return self.customer.name
        return self.customer_name_manual or '-'

    @property
    def display_customer_phone(self):
        if self.customer and self.customer.phone:
            return self.customer.phone
        return self.customer_phone_manual or '-'

    @property
    def display_customer_address(self):
        if self.customer and self.customer.address:
            return self.customer.address
        return self.customer_address_manual or '-'

    @property
    def display_contact_person(self):
        if self.customer and self.customer.contact_person:
            return self.customer.contact_person
        return self.contact_person_manual or '-'

    def __str__(self):
        return f"عرض سعر {self.id} - {self.display_customer_name}"

    def recalculate_totals(self):
        subtotal = sum((item.total for item in self.items.all()), Decimal('0'))
        discount_amount = subtotal * (self.discount_percent / Decimal('100'))
        net_before_vat = subtotal - discount_amount
        vat_amount = net_before_vat * (self.vat_percent / Decimal('100'))
        total_after_vat = net_before_vat + vat_amount

        Quotation.objects.filter(pk=self.pk).update(
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


class QuotationItem(models.Model):
    ITEM_TYPES = [
        ('Product', 'منتج'),
        ('Device', 'جهاز'),
        ('Spare Part', 'قطعة غيار'),
        ('Consumable', 'محلول / مستهلك'),
        ('Service', 'خدمة'),
        ('Visit', 'زيارة'),
        ('Other', 'أخرى'),
    ]

    quotation = models.ForeignKey(
        Quotation,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='عرض السعر'
    )

    item_type = models.CharField(max_length=20, choices=ITEM_TYPES, default='Product', verbose_name='نوع البند')

    inventory_item = models.ForeignKey(
        'app_inventory.InventoryItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quotation_items',
        verbose_name='الصنف المخزني'
    )

    maintenance_requirement = models.ForeignKey(
        'app_maintenance.MaintenanceRequirement',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quotation_items',
        verbose_name='احتياج الصيانة المرتبط'
    )

    description = models.CharField(max_length=255, verbose_name='وصف البند')
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1, verbose_name='الكمية')
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='سعر الوحدة')
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='إجمالي البند')

    class Meta:
        verbose_name = 'بند عرض سعر'
        verbose_name_plural = 'بنود عروض الأسعار'

    def __str__(self):
        return self.description

    def save(self, *args, **kwargs):
        if not self.description:
            if self.inventory_item:
                self.description = self.inventory_item.item_name
            elif self.maintenance_requirement:
                self.description = self.maintenance_requirement.item.item_name
            else:
                self.description = 'بند عرض سعر'

        self.total = self.quantity * self.price
        super().save(*args, **kwargs)

        if self.quotation_id:
            self.quotation.recalculate_totals()

    def delete(self, *args, **kwargs):
        quotation = self.quotation
        super().delete(*args, **kwargs)
        quotation.recalculate_totals()