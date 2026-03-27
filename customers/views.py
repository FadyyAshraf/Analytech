from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CustomerForm
from .models import Customer


def customer_list(request):
    query = request.GET.get('q', '').strip()
    customers = Customer.objects.all().order_by('name')

    if query:
        customers = customers.filter(
            Q(name__icontains=query) |
            Q(phone__icontains=query) |
            Q(contact_person__icontains=query) |
            Q(address__icontains=query)
        )

    return render(request, 'customers/customer_list.html', {
        'customers': customers,
        'query': query,
    })


def customer_create(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f'تم إضافة العميل {customer.name} بنجاح.')
            return redirect('customer_detail', customer_id=customer.id)
    else:
        form = CustomerForm()

    return render(request, 'customers/customer_form.html', {
        'form': form,
        'page_title': 'إضافة عميل جديد',
    })


def customer_edit(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)

    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تعديل بيانات العميل بنجاح.')
            return redirect('customer_detail', customer_id=customer.id)
    else:
        form = CustomerForm(instance=customer)

    return render(request, 'customers/customer_form.html', {
        'form': form,
        'page_title': f'تعديل العميل: {customer.name}',
    })


def customer_detail(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)

    account = getattr(customer, 'account', None)

    devices = customer.devices.all().order_by('device_name', 'serial_number')[:20]

    quotations = customer.quotations.select_related(
        'sales_owner',
        'commission_owner',
        'device'
    ).all().order_by('-id')[:10]

    invoices = []
    for quotation in quotations:
        if hasattr(quotation, 'invoice') and quotation.invoice:
            invoices.append(quotation.invoice)

    receipt_vouchers = customer.receipt_vouchers.select_related(
        'journal_entry'
    ).all().order_by('-voucher_date', '-id')[:10]

    maintenance_requests = customer.maintenance_requests.select_related(
        'device'
    ).all().order_by('-request_date', '-id')[:10]

    maintenance_visits = customer.maintenance_visits.select_related(
        'device',
        'engineer'
    ).all().order_by('-visit_date', '-id')[:10]

    preventive_plans = customer.preventive_plans.select_related(
        'device'
    ).all().order_by('next_due_date')[:10]

    employee_commissions = customer.employee_commissions.select_related(
        'employee',
        'invoice',
        'quotation'
    ).all().order_by('-commission_date', '-id')[:10]

    return render(request, 'customers/customer_detail.html', {
        'customer': customer,
        'account': account,
        'devices': devices,
        'quotations': quotations,
        'invoices': invoices,
        'receipt_vouchers': receipt_vouchers,
        'maintenance_requests': maintenance_requests,
        'maintenance_visits': maintenance_visits,
        'preventive_plans': preventive_plans,
        'employee_commissions': employee_commissions,
    })