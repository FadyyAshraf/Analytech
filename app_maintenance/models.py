from datetime import timedelta
from django.db import models
from django.utils import timezone

from customers.models import Customer
from app_devices.models import Device
from app_inventory.models import InventoryItem


class MaintenanceRequest(models.Model):
    PRIORITY_CHOICES = [
        ('Low', 'منخفضة'),
        ('Medium', 'متوسطة'),
        ('High', 'عالية'),
        ('Urgent', 'عاجلة'),
    ]

    STATUS_CHOICES = [
        ('New', 'جديد'),
        ('Assigned', 'تم التوزيع'),
        ('In Progress', 'قيد التنفيذ'),
        ('Waiting Approval', 'بانتظار موافقة العميل'),
        ('Waiting Parts', 'بانتظار قطع الغيار'),
        ('Resolved', 'تم الحل'),
        ('Closed', 'مغلق'),
    ]

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='maintenance_requests',
        verbose_name='العميل'
    )
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name='maintenance_requests',
        verbose_name='الجهاز'
    )

    request_date = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ البلاغ')
    reported_by = models.CharField(max_length=150, blank=True, null=True, verbose_name='اسم المُبلغ')
    contact_phone = models.CharField(max_length=50, blank=True, null=True, verbose_name='رقم التواصل')

    issue_description = models.TextField(verbose_name='وصف العطل / البلاغ')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Medium', verbose_name='الأولوية')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='New', verbose_name='الحالة')

    internal_notes = models.TextField(blank=True, null=True, verbose_name='ملاحظات داخلية')
    customer_notes = models.TextField(blank=True, null=True, verbose_name='ملاحظات العميل')

    class Meta:
        verbose_name = 'طلب صيانة'
        verbose_name_plural = 'طلبات الصيانة'
        ordering = ['-request_date', '-id']

    def __str__(self):
        return f"طلب صيانة #{self.id} - {self.customer.name} - {self.device.device_name}"


class PreventiveMaintenancePlan(models.Model):
    INTERVAL_TYPES = [
        ('Monthly', 'شهري'),
        ('Quarterly', 'كل 3 شهور'),
        ('SemiAnnual', 'كل 6 شهور'),
        ('Annual', 'سنوي'),
        ('CustomDays', 'عدد أيام مخصص'),
    ]

    device = models.OneToOneField(
        Device,
        on_delete=models.CASCADE,
        related_name='preventive_plan',
        verbose_name='الجهاز'
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='preventive_plans',
        verbose_name='العميل'
    )

    is_active = models.BooleanField(default=True, verbose_name='الخطة مفعلة')
    interval_type = models.CharField(max_length=20, choices=INTERVAL_TYPES, default='Quarterly', verbose_name='نوع الفترة')
    interval_days = models.PositiveIntegerField(default=90, verbose_name='عدد الأيام')
    start_date = models.DateField(default=timezone.localdate, verbose_name='بداية الجدول')
    last_visit_date = models.DateField(blank=True, null=True, verbose_name='آخر زيارة وقائية')
    next_due_date = models.DateField(blank=True, null=True, verbose_name='موعد الزيارة القادمة')
    grace_days = models.PositiveIntegerField(default=0, verbose_name='فترة سماح بالأيام')
    admin_notes = models.TextField(blank=True, null=True, verbose_name='ملاحظات الإدارة')

    class Meta:
        verbose_name = 'خطة صيانة وقائية'
        verbose_name_plural = 'خطط الصيانة الوقائية'
        ordering = ['next_due_date', 'device__device_name']

    def __str__(self):
        return f"{self.device.device_name} - خطة وقائية"

    def get_interval_days(self):
        if self.interval_type == 'Monthly':
            return 30
        if self.interval_type == 'Quarterly':
            return 90
        if self.interval_type == 'SemiAnnual':
            return 180
        if self.interval_type == 'Annual':
            return 365
        return self.interval_days or 90

    def calculate_next_due_date(self):
        base_date = self.last_visit_date or self.start_date or timezone.localdate()
        return base_date + timedelta(days=self.get_interval_days())

    def save(self, *args, **kwargs):
        if self.customer_id != self.device.customer_id:
            self.customer = self.device.customer
        if not self.next_due_date:
            self.next_due_date = self.calculate_next_due_date()
        super().save(*args, **kwargs)

    @property
    def is_due(self):
        return bool(self.next_due_date and self.next_due_date <= timezone.localdate())

    @property
    def is_overdue(self):
        if not self.next_due_date:
            return False
        return timezone.localdate() > (self.next_due_date + timedelta(days=self.grace_days))


class MaintenanceVisit(models.Model):
    VISIT_TYPES = [
        ('Emergency', 'طارئة'),
        ('Preventive', 'دورية وقائية'),
        ('Follow-up', 'متابعة'),
        ('Installation', 'تركيب'),
        ('Training', 'تدريب'),
    ]

    STATUS_CHOICES = [
        ('Open', 'مفتوحة'),
        ('Inspection Done', 'تم الفحص'),
        ('Waiting Approval', 'بانتظار موافقة العميل'),
        ('Waiting Parts', 'بانتظار قطع الغيار'),
        ('Scheduled Follow-up', 'مجدولة لزيارة أخرى'),
        ('Resolved', 'تم الحل'),
        ('Closed', 'مغلقة'),
    ]

    request = models.ForeignKey(
        MaintenanceRequest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='visits',
        verbose_name='طلب الصيانة'
    )

    preventive_plan = models.ForeignKey(
        PreventiveMaintenancePlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='visits',
        verbose_name='خطة الصيانة الوقائية'
    )

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='maintenance_visits',
        verbose_name='العميل'
    )

    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name='maintenance_visits',
        verbose_name='الجهاز'
    )

    visit_type = models.CharField(max_length=30, choices=VISIT_TYPES, verbose_name='نوع الزيارة')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Open', verbose_name='الحالة')

    visit_date = models.DateField(default=timezone.localdate, verbose_name='تاريخ الزيارة')
    next_visit_date = models.DateField(blank=True, null=True, verbose_name='الزيارة القادمة')

    engineer = models.ForeignKey(
        'app_employees.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='maintenance_visits',
        verbose_name='المهندس المسؤول'
    )

    engineer_name = models.CharField(max_length=150, blank=True, null=True, verbose_name='اسم المهندس القائم بالعمل')

    signed_report_received = models.BooleanField(default=False, verbose_name='تم استلام تقرير موقع من العميل')
    signed_report_date = models.DateField(blank=True, null=True, verbose_name='تاريخ التقرير الموقع')

    device_condition_before = models.TextField(blank=True, null=True, verbose_name='حالة الجهاز قبل الصيانة')
    issue_found = models.TextField(blank=True, null=True, verbose_name='العطل / الملاحظات المكتشفة')
    work_performed = models.TextField(blank=True, null=True, verbose_name='الأعمال التي تم تنفيذها')
    device_condition_after = models.TextField(blank=True, null=True, verbose_name='حالة الجهاز بعد الصيانة')
    final_result = models.TextField(blank=True, null=True, verbose_name='النتيجة النهائية / التقرير الفني')

    issue_resolved = models.BooleanField(default=False, verbose_name='هل تم حل المشكلة؟')
    needs_spare_parts = models.BooleanField(default=False, verbose_name='هل يحتاج قطع غيار؟')
    requires_customer_approval = models.BooleanField(default=False, verbose_name='هل يحتاج موافقة العميل على عرض السعر؟')

    notes = models.TextField(blank=True, null=True, verbose_name='ملاحظات إضافية')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'زيارة صيانة'
        verbose_name_plural = 'زيارات الصيانة'
        ordering = ['-visit_date', '-id']

    def __str__(self):
        return f"زيارة #{self.id} - {self.device.device_name} - {self.visit_date}"

    def save(self, *args, **kwargs):
        if self.engineer and not self.engineer_name:
            self.engineer_name = self.engineer.full_name
        super().save(*args, **kwargs)


class MaintenanceRequirement(models.Model):
    AVAILABILITY_CHOICES = [
        ('Unknown', 'غير محدد'),
        ('Available', 'متاح'),
        ('Not Available', 'غير متاح'),
        ('Ordered', 'تم طلبه'),
    ]

    QUOTATION_STATUS_CHOICES = [
        ('Not Needed', 'لا يحتاج عرض سعر'),
        ('Draft', 'قيد الإعداد'),
        ('Sent', 'تم الإرسال'),
        ('Approved', 'تمت الموافقة'),
        ('Rejected', 'مرفوض'),
    ]

    visit = models.ForeignKey(
        MaintenanceVisit,
        on_delete=models.CASCADE,
        related_name='requirements',
        verbose_name='الزيارة'
    )

    item = models.ForeignKey(
        InventoryItem,
        on_delete=models.CASCADE,
        verbose_name='الصنف / قطعة الغيار'
    )

    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1, verbose_name='الكمية المطلوبة')
    availability_status = models.CharField(
        max_length=20,
        choices=AVAILABILITY_CHOICES,
        default='Unknown',
        verbose_name='حالة التوفر'
    )

    quotation_required = models.BooleanField(default=False, verbose_name='هل يحتاج عرض سعر؟')
    quotation_status = models.CharField(
        max_length=20,
        choices=QUOTATION_STATUS_CHOICES,
        default='Not Needed',
        verbose_name='حالة عرض السعر'
    )

    approved_by_customer = models.BooleanField(default=False, verbose_name='تمت موافقة العميل')
    installed = models.BooleanField(default=False, verbose_name='تم التركيب')
    linked_invoice = models.ForeignKey(
        'app_invoices.Invoice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='maintenance_requirements',
        verbose_name='الفاتورة المرتبطة'
    )

    notes = models.TextField(blank=True, null=True, verbose_name='ملاحظات')

    class Meta:
        verbose_name = 'احتياج صيانة / قطعة مطلوبة'
        verbose_name_plural = 'احتياجات الصيانة / القطع المطلوبة'

    def __str__(self):
        return f"{self.item.item_name} - {self.quantity}"