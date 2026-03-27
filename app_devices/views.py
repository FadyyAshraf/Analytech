from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import DeviceForm
from .models import Device


def device_list(request):
    query = request.GET.get('q', '').strip()

    devices = Device.objects.select_related('customer').all().order_by('device_name', 'serial_number')

    if query:
        devices = devices.filter(
            Q(device_name__icontains=query) |
            Q(serial_number__icontains=query) |
            Q(model__icontains=query) |
            Q(customer__name__icontains=query)
        )

    return render(request, 'devices/device_list.html', {
        'devices': devices,
        'query': query,
    })


def device_create(request):
    if request.method == 'POST':
        form = DeviceForm(request.POST)
        if form.is_valid():
            device = form.save()
            messages.success(request, 'تم إضافة الجهاز بنجاح.')
            return redirect('device_detail', device_id=device.id)
    else:
        form = DeviceForm()

    return render(request, 'devices/device_form.html', {
        'form': form,
        'page_title': 'إضافة جهاز جديد',
    })


def device_edit(request, device_id):
    device = get_object_or_404(Device, pk=device_id)

    if request.method == 'POST':
        form = DeviceForm(request.POST, instance=device)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تعديل الجهاز بنجاح.')
            return redirect('device_detail', device_id=device.id)
    else:
        form = DeviceForm(instance=device)

    return render(request, 'devices/device_form.html', {
        'form': form,
        'page_title': f'تعديل الجهاز: {device.device_name}',
    })


def device_detail(request, device_id):
    device = get_object_or_404(Device.objects.select_related('customer'), pk=device_id)

    quotations = device.quotations.select_related(
        'customer',
        'sales_owner',
        'commission_owner'
    ).all().order_by('-id')[:10]

    invoices = []
    for quotation in quotations:
        if hasattr(quotation, 'invoice') and quotation.invoice:
            invoices.append(quotation.invoice)

    maintenance_requests = device.maintenance_requests.select_related(
        'customer'
    ).all().order_by('-request_date', '-id')[:10]

    maintenance_visits = device.maintenance_visits.select_related(
        'customer',
        'engineer'
    ).all().order_by('-visit_date', '-id')[:10]

    preventive_plan = getattr(device, 'preventive_plan', None)

    return render(request, 'devices/device_detail.html', {
        'device': device,
        'quotations': quotations,
        'invoices': invoices,
        'maintenance_requests': maintenance_requests,
        'maintenance_visits': maintenance_visits,
        'preventive_plan': preventive_plan,
    })