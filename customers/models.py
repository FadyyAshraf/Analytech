from django.db import models, transaction


class Customer(models.Model):
    CUSTOMER_TYPES = [
        ('Lab', 'معمل'),
        ('Hospital', 'مستشفى'),
        ('Distributor', 'موزع'),
        ('Other', 'أخرى'),
    ]

    name = models.CharField(max_length=200, verbose_name='اسم العميل')
    customer_type = models.CharField(max_length=20, choices=CUSTOMER_TYPES, verbose_name='نوع العميل')
    address = models.TextField(blank=True, null=True, verbose_name='العنوان')
    phone = models.CharField(max_length=50, blank=True, null=True, verbose_name='الهاتف')
    contact_person = models.CharField(max_length=150, blank=True, null=True, verbose_name='الشخص المسؤول')

    account = models.OneToOneField(
        'accounting.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customer',
        verbose_name='الحساب المحاسبي'
    )

    notes = models.TextField(blank=True, null=True, verbose_name='ملاحظات')

    class Meta:
        verbose_name = 'عميل'
        verbose_name_plural = 'العملاء'
        ordering = ['name']

    def __str__(self):
        return self.name

    def _generate_customer_account_code(self):
        from accounting.models import Account

        existing_codes = []
        for acc in Account.objects.filter(account_type='Asset'):
            if acc.code and acc.code.isdigit():
                code_int = int(acc.code)
                if 1101 <= code_int <= 1999:
                    existing_codes.append(code_int)

        if existing_codes:
            next_code = max(existing_codes) + 1
        else:
            next_code = 1101

        return str(next_code)

    @transaction.atomic
    def create_account_if_missing(self):
        from accounting.models import Account

        if self.account_id:
            return self.account

        parent_account = Account.objects.filter(code='1100').first()

        account = Account.objects.create(
            code=self._generate_customer_account_code(),
            name=f'العميل - {self.name}',
            account_type='Asset',
            parent=parent_account,
            is_active=True,
            notes=f'حساب عميل مرتبط بـ {self.name}'
        )

        self.account = account
        Customer.objects.filter(pk=self.pk).update(account=account)
        return account

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new and not self.account_id:
            self.create_account_if_missing()