from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from app_devices.models import Device
from .forms import (
    MaintenanceRequestForm,
    PreventiveMaintenancePlanForm,
    MaintenanceVisitForm,
)
from .models import (
    MaintenanceRequest,
    PreventiveMaintenancePlan,
    MaintenanceVisit,
)


def maintenance_request_list(request):
    query = request.GET.get('q', '').strip()
    requests = MaintenanceRequest.objects.select_related('customer', 'device').all().order_by('-request_date', '-id')

    if query:
        requests = requests.filter(
            Q(customer__name__icontains=query) |
            Q(device__device_name__icontains=query) |
            Q(device__serial_number__icontains=query) |
            Q(issue_description__icontains=query)
        )

    return render(request, 'maintenance/request_list.html', {
        'requests': requests,
        'query': query,
    })


def maintenance_request_create(request):
    if request.method == 'POST':
        form = MaintenanceRequestForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم إضافة طلب الصيانة بنجاح.')
            return redirect('maintenance_request_list')
    else:
        form = MaintenanceRequestForm()

    return render(request, 'maintenance/request_form.html', {
        'form': form,
        'page_title': 'طلب صيانة جديد',
    })


def maintenance_request_edit(request, request_id):
    obj = get_object_or_404(MaintenanceRequest, pk=request_id)

    if request.method == 'POST':
        form = MaintenanceRequestForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تعديل طلب الصيانة بنجاح.')
            return redirect('maintenance_request_list')
    else:
        form = MaintenanceRequestForm(instance=obj)

    return render(request, 'maintenance/request_form.html', {
        'form': form,
        'page_title': f'تعديل طلب الصيانة رقم {obj.id}',
    })


def preventive_plan_list(request):
    query = request.GET.get('q', '').strip()
    plans = PreventiveMaintenancePlan.objects.select_related('customer', 'device').all().order_by('next_due_date', 'device__device_name')

    if query:
        plans = plans.filter(
            Q(customer__name__icontains=query) |
            Q(device__device_name__icontains=query) |
            Q(device__serial_number__icontains=query)
        )

    return render(request, 'maintenance/preventive_plan_list.html', {
        'plans': plans,
        'query': query,
    })


def preventive_plan_create(request):
    if request.method == 'POST':
        form = PreventiveMaintenancePlanForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم إضافة خطة الصيانة الوقائية بنجاح.')
            return redirect('preventive_plan_list')
    else:
        form = PreventiveMaintenancePlanForm()

    return render(request, 'maintenance/preventive_plan_form.html', {
        'form': form,
        'page_title': 'خطة صيانة وقائية جديدة',
    })


def preventive_plan_edit(request, plan_id):
    obj = get_object_or_404(PreventiveMaintenancePlan, pk=plan_id)

    if request.method == 'POST':
        form = PreventiveMaintenancePlanForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تعديل خطة الصيانة الوقائية بنجاح.')
            return redirect('preventive_plan_list')
    else:
        form = PreventiveMaintenancePlanForm(instance=obj)

    return render(request, 'maintenance/preventive_plan_form.html', {
        'form': form,
        'page_title': f'تعديل خطة الصيانة للجهاز {obj.device.device_name}',
    })


def preventive_plan_sync(request):
    devices = Device.objects.select_related('customer').all()
    created_count = 0

    for device in devices:
        if not hasattr(device, 'preventive_plan') and device.customer:
            PreventiveMaintenancePlan.objects.create(
                device=device,
                customer=device.customer,
                interval_type='Quarterly',
                interval_days=90,
                start_date=device.installation_date or timezone.localdate()
            )
            created_count += 1

    messages.success(request, f'تمت مزامنة الخطط الوقائية. تم إنشاء {created_count} خطة جديدة.')
    return redirect('preventive_plan_list')


def maintenance_visit_list(request):
    query = request.GET.get('q', '').strip()
    visits = MaintenanceVisit.objects.select_related('customer', 'device', 'engineer').all().order_by('-visit_date', '-id')

    if query:
        visits = visits.filter(
            Q(customer__name__icontains=query) |
            Q(device__device_name__icontains=query) |
            Q(device__serial_number__icontains=query) |
            Q(engineer__full_name__icontains=query) |
            Q(engineer_name__icontains=query)
        )

    return render(request, 'maintenance/visit_list.html', {
        'visits': visits,
        'query': query,
    })


def maintenance_visit_create(request):
    if request.method == 'POST':
        form = MaintenanceVisitForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم إضافة زيارة الصيانة بنجاح.')
            return redirect('maintenance_visit_list')
    else:
        form = MaintenanceVisitForm()

    return render(request, 'maintenance/visit_form.html', {
        'form': form,
        'page_title': 'زيارة صيانة جديدة',
    })


def maintenance_visit_edit(request, visit_id):
    obj = get_object_or_404(MaintenanceVisit, pk=visit_id)

    if request.method == 'POST':
        form = MaintenanceVisitForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تعديل زيارة الصيانة بنجاح.')
            return redirect('maintenance_visit_list')
    else:
        form = MaintenanceVisitForm(instance=obj)

    return render(request, 'maintenance/visit_form.html', {
        'form': form,
        'page_title': f'تعديل زيارة الصيانة رقم {obj.id}',
    })


def maintenance_reports_dashboard(request):
    total_plans = PreventiveMaintenancePlan.objects.count()
    overdue_count = sum(1 for p in PreventiveMaintenancePlan.objects.all() if p.is_overdue)
    due_now_count = sum(1 for p in PreventiveMaintenancePlan.objects.all() if p.is_due and not p.is_overdue)

    open_requests_count = MaintenanceRequest.objects.exclude(
        status__in=['Resolved', 'Closed']
    ).count()

    waiting_parts_count = MaintenanceVisit.objects.filter(
        status='Waiting Parts'
    ).count()

    completed_preventive_count = MaintenanceVisit.objects.filter(
        visit_type='Preventive'
    ).count()

    engineers_count = MaintenanceVisit.objects.exclude(
        engineer__isnull=True
    ).values('engineer').distinct().count()

    recent_visits = MaintenanceVisit.objects.select_related(
        'customer', 'device', 'engineer'
    ).all().order_by('-visit_date', '-id')[:10]

    return render(request, 'maintenance/reports_dashboard.html', {
        'total_plans': total_plans,
        'overdue_count': overdue_count,
        'due_now_count': due_now_count,
        'open_requests_count': open_requests_count,
        'waiting_parts_count': waiting_parts_count,
        'completed_preventive_count': completed_preventive_count,
        'engineers_count': engineers_count,
        'recent_visits': recent_visits,
    })


def overdue_preventive_customers_report(request):
    plans = PreventiveMaintenancePlan.objects.select_related(
        'customer', 'device'
    ).all().order_by('next_due_date', 'customer__name')

    rows = [p for p in plans if p.is_overdue]

    return render(request, 'maintenance/report_preventive_overdue.html', {
        'rows': rows,
    })


def completed_preventive_customers_report(request):
    rows = MaintenanceVisit.objects.select_related(
        'customer', 'device', 'engineer', 'preventive_plan'
    ).filter(
        visit_type='Preventive'
    ).order_by('-visit_date', '-id')

    return render(request, 'maintenance/report_preventive_done.html', {
        'rows': rows,
    })


def engineer_performance_report(request):
    engineers_data = []

    visits = MaintenanceVisit.objects.select_related('engineer', 'customer', 'device').all()

    by_engineer = {}
    for visit in visits:
        key = visit.engineer.id if visit.engineer else f'name:{visit.engineer_name or "-"}'
        if key not in by_engineer:
            by_engineer[key] = {
                'engineer': visit.engineer,
                'engineer_name': visit.engineer.full_name if visit.engineer else (visit.engineer_name or '-'),
                'total_visits': 0,
                'preventive_visits': 0,
                'emergency_visits': 0,
                'resolved_visits': 0,
                'waiting_parts_visits': 0,
                'customers': set(),
            }

        row = by_engineer[key]
        row['total_visits'] += 1

        if visit.visit_type == 'Preventive':
            row['preventive_visits'] += 1
        if visit.visit_type == 'Emergency':
            row['emergency_visits'] += 1
        if visit.status in ['Resolved', 'Closed']:
            row['resolved_visits'] += 1
        if visit.status == 'Waiting Parts':
            row['waiting_parts_visits'] += 1

        row['customers'].add(visit.customer.name)

    for row in by_engineer.values():
        row['customers_count'] = len(row['customers'])
        row['customers_list'] = '، '.join(sorted(row['customers']))
        engineers_data.append(row)

    engineers_data.sort(key=lambda x: x['total_visits'], reverse=True)

    return render(request, 'maintenance/report_engineers.html', {
        'rows': engineers_data,
    })