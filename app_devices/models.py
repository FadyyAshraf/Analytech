from django.db import models
from customers.models import Customer


class Device(models.Model):
    DEVICE_TYPES = [
        ('CBC', 'CBC'),
        ('Chemistry', 'Chemistry'),
        ('Immunoassay', 'Immunoassay'),
        ('Coagulation', 'Coagulation'),
        ('Other', 'Other'),
    ]

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='devices',
        verbose_name='العميل'
    )
    device_name = models.CharField(max_length=200, verbose_name='اسم الجهاز')
    device_type = models.CharField(max_length=50, choices=DEVICE_TYPES, default='CBC', verbose_name='نوع الجهاز')
    model = models.CharField(max_length=150, blank=True, null=True, verbose_name='الموديل')
    serial_number = models.CharField(max_length=150, unique=True, verbose_name='السيريال نمبر')
    installation_date = models.DateField(blank=True, null=True, verbose_name='تاريخ التركيب')
    warranty_end_date = models.DateField(blank=True, null=True, verbose_name='نهاية الضمان')
    notes = models.TextField(blank=True, null=True, verbose_name='ملاحظات')

    class Meta:
        verbose_name = 'جهاز'
        verbose_name_plural = 'الأجهزة'
        ordering = ['device_name', 'serial_number']

    def __str__(self):
        return f"{self.device_name} - {self.serial_number}"