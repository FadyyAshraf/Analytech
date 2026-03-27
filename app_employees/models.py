from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Employee(models.Model):
    STATUS_CHOICES = [
        ('Active', 'نشط'),
        ('On Leave', 'إجازة'),
        ('Suspended', 'موقوف'),
        ('Resigned', 'مستقيل'),
    ]

    employee_code = models.CharField(max_length=50, unique=True, verbose_name='كود الموظف')
    full_name = models.CharField(max_length=200, verbose_name='اسم الموظف')
    department = models.CharField(max_length=100, blank=True, null=True, verbose_name='القسم')
    job_title = models.CharField(max_length=150, blank=True, null=True, verbose_name='الوظيفة')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active', verbose_name='الحالة')

    hire_date = models.DateField(default=timezone.localdate, verbose_name='تاريخ التعيين')
    birth_date = models.DateField(blank=True, null=True, verbose_name='تاريخ الميلاد')

    national_id = models.CharField(max_length=50, blank=True, null=True, verbose_name='الرقم القومي')
    phone = models.CharField(max_length=50, blank=True, null=True, verbose_name='الموبايل')
    email = models.EmailField(blank=True, null=True, verbose_name='البريد الإلكتروني')
    address = models.TextField(blank=True, null=True, verbose_name='العنوان')

    qualification = models.CharField(max_length=200, blank=True, null=True, verbose_name='المؤهل الدراسي')
    specialization = models.CharField(max_length=200, blank=True, null=True, verbose_name='التخصص')

    direct_manager = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='team_members',
        verbose_name='المدير المباشر'
    )

    can_do_sales = models.BooleanField(default=False, verbose_name='يمكنه تنفيذ مبيعات')
    can_do_service = models.BooleanField(default=False, verbose_name='يمكنه تنفيذ صيانة')
    can_manage_team = models.BooleanField(default=False, verbose_name='يمكنه إدارة فريق')

    sales_commission_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='نسبة عمولة المبيعات الافتراضية %'
    )

    notes = models.TextField(blank=True, null=True, verbose_name='ملاحظات')

    class Meta:
        verbose_name = 'موظف'
        verbose_name_plural = 'الموظفون'
        ordering = ['full_name']

    def __str__(self):
        return f'{self.employee_code} - {self.full_name}'


class EmployeeRole(models.Model):
    ROLE_CHOICES = [
        ('Sales Rep', 'مندوب مبيعات'),
        ('Sales Manager', 'مدير مبيعات'),
        ('Service Engineer', 'مهندس صيانة'),
        ('Service Manager', 'مدير صيانة'),
        ('Accountant', 'محاسب'),
        ('Admin', 'إداري'),
        ('Other', 'أخرى'),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='roles',
        verbose_name='الموظف'
    )
    role_name = models.CharField(max_length=50, choices=ROLE_CHOICES, verbose_name='الدور')
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    notes = models.TextField(blank=True, null=True, verbose_name='ملاحظات')

    class Meta:
        verbose_name = 'دور موظف'
        verbose_name_plural = 'أدوار الموظفين'

    def __str__(self):
        return f'{self.employee.full_name} - {self.role_name}'


class EmployeeCompensation(models.Model):
    PAYMENT_METHODS = [
        ('Cash', 'نقدي'),
        ('Bank', 'بنك'),
        ('Transfer', 'تحويل'),
        ('Other', 'أخرى'),
    ]

    employee = models.OneToOneField(
        Employee,
        on_delete=models.CASCADE,
        related_name='compensation',
        verbose_name='الموظف'
    )

    basic_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='المرتب الأساسي')
    transport_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='بدل انتقال')
    phone_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='بدل موبايل')
    housing_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='بدل سكن')
    other_allowances = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='بدلات أخرى')

    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='Cash', verbose_name='طريقة الصرف')
    bank_name = models.CharField(max_length=150, blank=True, null=True, verbose_name='اسم البنك')
    bank_account = models.CharField(max_length=150, blank=True, null=True, verbose_name='رقم الحساب')
    effective_from = models.DateField(default=timezone.localdate, verbose_name='ساري من')

    is_active = models.BooleanField(default=True, verbose_name='نشط')

    class Meta:
        verbose_name = 'بيانات مالية للموظف'
        verbose_name_plural = 'البيانات المالية للموظفين'

    def __str__(self):
        return f'البيانات المالية - {self.employee.full_name}'

    @property
    def total_fixed(self):
        return (
            self.basic_salary +
            self.transport_allowance +
            self.phone_allowance +
            self.housing_allowance +
            self.other_allowances
        )


class EmployeePenalty(models.Model):
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='penalties',
        verbose_name='الموظف'
    )
    penalty_date = models.DateField(default=timezone.localdate, verbose_name='تاريخ الجزاء')
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='قيمة الجزاء')
    reason = models.CharField(max_length=255, verbose_name='سبب الجزاء')
    notes = models.TextField(blank=True, null=True, verbose_name='ملاحظات')

    class Meta:
        verbose_name = 'جزاء'
        verbose_name_plural = 'الجزاءات'
        ordering = ['-penalty_date', '-id']

    def __str__(self):
        return f'جزاء - {self.employee.full_name} - {self.amount}'


class EmployeeBonus(models.Model):
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='bonuses',
        verbose_name='الموظف'
    )
    bonus_date = models.DateField(default=timezone.localdate, verbose_name='تاريخ الحافز/المكافأة')
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='القيمة')
    reason = models.CharField(max_length=255, verbose_name='السبب')
    notes = models.TextField(blank=True, null=True, verbose_name='ملاحظات')

    class Meta:
        verbose_name = 'حافز / مكافأة'
        verbose_name_plural = 'الحوافز والمكافآت'
        ordering = ['-bonus_date', '-id']

    def __str__(self):
        return f'حافز - {self.employee.full_name} - {self.amount}'


class EmployeeExpenseClaim(models.Model):
    EXPENSE_TYPES = [
        ('Transport', 'انتقالات'),
        ('Meals', 'إقامة / وجبات'),
        ('Maintenance', 'مصروفات تشغيل'),
        ('Sales', 'مصروفات مبيعات'),
        ('Other', 'أخرى'),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='expense_claims',
        verbose_name='الموظف'
    )
    expense_date = models.DateField(default=timezone.localdate, verbose_name='تاريخ المصروف')
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='القيمة')
    expense_type = models.CharField(max_length=30, choices=EXPENSE_TYPES, default='Other', verbose_name='نوع المصروف')
    description = models.CharField(max_length=255, verbose_name='البيان')
    approved = models.BooleanField(default=False, verbose_name='معتمد')
    notes = models.TextField(blank=True, null=True, verbose_name='ملاحظات')

    class Meta:
        verbose_name = 'مصروف مسترد'
        verbose_name_plural = 'المصروفات المستردة'
        ordering = ['-expense_date', '-id']

    def __str__(self):
        return f'{self.employee.full_name} - {self.amount}'


class EmployeeAdvance(models.Model):
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='advances',
        verbose_name='الموظف'
    )
    advance_date = models.DateField(default=timezone.localdate, verbose_name='تاريخ السلفة')
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='قيمة السلفة')
    description = models.CharField(max_length=255, blank=True, null=True, verbose_name='البيان')
    settled_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='المسدد منها')
    notes = models.TextField(blank=True, null=True, verbose_name='ملاحظات')

    class Meta:
        verbose_name = 'سلفة'
        verbose_name_plural = 'السلف'
        ordering = ['-advance_date', '-id']

    def __str__(self):
        return f'سلفة - {self.employee.full_name} - {self.amount}'

    @property
    def remaining_amount(self):
        return self.amount - self.settled_amount


class EmployeeCommission(models.Model):
    STATUS_CHOICES = [
        ('Draft', 'مسودة'),
        ('Approved', 'معتمدة'),
        ('Paid', 'مدفوعة'),
        ('Cancelled', 'ملغاة'),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='commissions',
        verbose_name='الموظف'
    )

    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employee_commissions',
        verbose_name='العميل'
    )

    quotation = models.ForeignKey(
        'app_quotations.Quotation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employee_commissions',
        verbose_name='عرض السعر'
    )

    invoice = models.ForeignKey(
        'app_invoices.Invoice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employee_commissions',
        verbose_name='الفاتورة'
    )

    commission_date = models.DateField(default=timezone.localdate, verbose_name='تاريخ العمولة')
    base_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='قيمة الأساس')
    commission_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='نسبة العمولة %')
    commission_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='قيمة العمولة')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft', verbose_name='الحالة')
    notes = models.TextField(blank=True, null=True, verbose_name='ملاحظات')

    class Meta:
        verbose_name = 'عمولة'
        verbose_name_plural = 'العمولات'
        ordering = ['-commission_date', '-id']

    def __str__(self):
        return f'عمولة - {self.employee.full_name} - {self.commission_amount}'

    def clean(self):
        if self.commission_percent < 0:
            raise ValidationError('نسبة العمولة لا يجوز أن تكون سالبة.')

    def save(self, *args, **kwargs):
        self.commission_amount = (self.base_amount * self.commission_percent) / Decimal('100')
        super().save(*args, **kwargs)


class EmployeePayroll(models.Model):
    STATUS_CHOICES = [
        ('Draft', 'مسودة'),
        ('Approved', 'معتمد'),
        ('Paid', 'مدفوع'),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='payrolls',
        verbose_name='الموظف'
    )
    month = models.PositiveIntegerField(verbose_name='الشهر')
    year = models.PositiveIntegerField(verbose_name='السنة')

    basic_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='الأساسي')
    allowances_total = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='إجمالي البدلات')
    bonuses_total = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='إجمالي الحوافز')
    commissions_total = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='إجمالي العمولات')
    expenses_total = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='إجمالي المصروفات')
    penalties_total = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='إجمالي الجزاءات')
    advances_total = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='إجمالي السلف')
    net_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='صافي المستحق')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft', verbose_name='الحالة')
    notes = models.TextField(blank=True, null=True, verbose_name='ملاحظات')

    class Meta:
        verbose_name = 'مسير راتب'
        verbose_name_plural = 'مسيرات الرواتب'
        ordering = ['-year', '-month', 'employee__full_name']
        unique_together = ('employee', 'month', 'year')

    def __str__(self):
        return f'مسير {self.employee.full_name} - {self.month}/{self.year}'

    def generate_totals(self):
        compensation = getattr(self.employee, 'compensation', None)

        basic_salary = compensation.basic_salary if compensation else Decimal('0')
        allowances_total = Decimal('0')
        if compensation:
            allowances_total = (
                compensation.transport_allowance +
                compensation.phone_allowance +
                compensation.housing_allowance +
                compensation.other_allowances
            )

        bonuses_total = sum(
            (x.amount for x in self.employee.bonuses.filter(
                bonus_date__month=self.month,
                bonus_date__year=self.year
            )),
            Decimal('0')
        )

        commissions_total = sum(
            (x.commission_amount for x in self.employee.commissions.filter(
                commission_date__month=self.month,
                commission_date__year=self.year,
                status__in=['Approved', 'Paid']
            )),
            Decimal('0')
        )

        expenses_total = sum(
            (x.amount for x in self.employee.expense_claims.filter(
                expense_date__month=self.month,
                expense_date__year=self.year,
                approved=True
            )),
            Decimal('0')
        )

        penalties_total = sum(
            (x.amount for x in self.employee.penalties.filter(
                penalty_date__month=self.month,
                penalty_date__year=self.year
            )),
            Decimal('0')
        )

        advances_total = sum(
            (x.amount for x in self.employee.advances.filter(
                advance_date__month=self.month,
                advance_date__year=self.year
            )),
            Decimal('0')
        )

        self.basic_salary = basic_salary
        self.allowances_total = allowances_total
        self.bonuses_total = bonuses_total
        self.commissions_total = commissions_total
        self.expenses_total = expenses_total
        self.penalties_total = penalties_total
        self.advances_total = advances_total

        self.net_salary = (
            self.basic_salary +
            self.allowances_total +
            self.bonuses_total +
            self.commissions_total +
            self.expenses_total -
            self.penalties_total -
            self.advances_total
        )

    def save(self, *args, **kwargs):
        self.generate_totals()
        super().save(*args, **kwargs)