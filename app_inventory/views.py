from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from app_maintenance.models import PreventiveMaintenancePlan, MaintenanceRequest, MaintenanceVisit
from .forms import (
    InventoryItemForm,
    InventoryLotForm,
    InventoryTransactionForm,
    RecallNoticeForm,
)
from .models import InventoryItem, InventoryLot, InventoryTransaction, RecallNotice


def dashboard(request):
    total_items = InventoryItem.objects.count()
    low_stock_items = InventoryItem.objects.filter(quantity__lte=0)
    recent_transactions = InventoryTransaction.objects.select_related('item', 'lot').all().order_by('-transaction_date', '-id')[:10]
    expiring_lots = [lot for lot in InventoryLot.objects.select_related('item').all() if lot.is_expiring_soon()]
    recall_open = RecallNotice.objects.filter(status__in=['Open', 'In Progress']).count()

    active_plans = PreventiveMaintenancePlan.objects.select_related('customer', 'device').filter(is_active=True)
    maintenance_due_count = sum(1 for plan in active_plans if plan.is_due and not plan.is_overdue)
    maintenance_overdue_count = sum(1 for plan in active_plans if plan.is_overdue)

    maintenance_open_requests = MaintenanceRequest.objects.exclude(
        status__in=['Resolved', 'Closed']
    ).count()

    maintenance_waiting_parts = MaintenanceVisit.objects.filter(
        status='Waiting Parts'
    ).count()

    return render(request, 'dashboard.html', {
        'total_items': total_items,
        'low_stock_count': low_stock_items.count(),
        'recent_transactions': recent_transactions,
        'expiring_lots_count': len(expiring_lots),
        'recall_open_count': recall_open,
        'maintenance_due_count': maintenance_due_count,
        'maintenance_overdue_count': maintenance_overdue_count,
        'maintenance_open_requests': maintenance_open_requests,
        'maintenance_waiting_parts': maintenance_waiting_parts,
    })


def inventory_dashboard(request):
    items = InventoryItem.objects.all()
    lots = InventoryLot.objects.select_related('item').all()
    transactions = InventoryTransaction.objects.select_related('item', 'lot').all().order_by('-transaction_date', '-id')[:10]
    recalls = RecallNotice.objects.filter(status__in=['Open', 'In Progress']).count()

    low_stock_items = items.filter(quantity__lte=0)
    expiring_lots = [lot for lot in lots if lot.is_expiring_soon()]

    return render(request, 'app_inventory/inventory_dashboard.html', {
        'total_items': items.count(),
        'low_stock_count': low_stock_items.count(),
        'expiring_lots_count': len(expiring_lots),
        'open_recalls_count': recalls,
        'recent_transactions': transactions,
    })


def item_list(request):
    query = request.GET.get('q', '')
    items = InventoryItem.objects.all().order_by('item_name')

    if query:
        items = items.filter(
            Q(item_name__icontains=query) |
            Q(item_code__icontains=query) |
            Q(item_type__icontains=query) |
            Q(supplier__icontains=query)
        )

    return render(request, 'app_inventory/item_list.html', {
        'items': items,
        'query': query,
    })


def item_create(request):
    if request.method == 'POST':
        form = InventoryItemForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم إضافة الصنف بنجاح.')
            return redirect('inventory_item_list')
    else:
        form = InventoryItemForm()

    return render(request, 'app_inventory/item_form.html', {
        'form': form,
        'page_title': 'إضافة صنف جديد',
    })


def item_edit(request, item_id):
    item = get_object_or_404(InventoryItem, pk=item_id)

    if request.method == 'POST':
        form = InventoryItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تعديل الصنف بنجاح.')
            return redirect('inventory_item_list')
    else:
        form = InventoryItemForm(instance=item)

    return render(request, 'app_inventory/item_form.html', {
        'form': form,
        'page_title': f'تعديل الصنف: {item.item_name}',
    })


def lot_list(request):
    query = request.GET.get('q', '')
    lots = InventoryLot.objects.select_related('item').all().order_by('item__item_name', 'lot_number')

    if query:
        lots = lots.filter(
            Q(item__item_name__icontains=query) |
            Q(item__item_code__icontains=query) |
            Q(lot_number__icontains=query)
        )

    return render(request, 'app_inventory/lot_list.html', {
        'lots': lots,
        'query': query,
    })


def lot_create(request):
    if request.method == 'POST':
        form = InventoryLotForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم إضافة التشغيلة بنجاح.')
            return redirect('inventory_lot_list')
    else:
        form = InventoryLotForm()

    return render(request, 'app_inventory/lot_form.html', {
        'form': form,
        'page_title': 'إضافة تشغيلة جديدة',
    })


def lot_edit(request, lot_id):
    lot = get_object_or_404(InventoryLot, pk=lot_id)

    if request.method == 'POST':
        form = InventoryLotForm(request.POST, instance=lot)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تعديل التشغيلة بنجاح.')
            return redirect('inventory_lot_list')
    else:
        form = InventoryLotForm(instance=lot)

    return render(request, 'app_inventory/lot_form.html', {
        'form': form,
        'page_title': f'تعديل التشغيلة: {lot.lot_number}',
    })


def transaction_list(request):
    query = request.GET.get('q', '')
    transactions = InventoryTransaction.objects.select_related('item', 'lot').all().order_by('-transaction_date', '-id')

    if query:
        transactions = transactions.filter(
            Q(item__item_name__icontains=query) |
            Q(item__item_code__icontains=query) |
            Q(lot__lot_number__icontains=query) |
            Q(source_name__icontains=query) |
            Q(reference__icontains=query)
        )

    return render(request, 'app_inventory/transaction_list.html', {
        'transactions': transactions,
        'query': query,
    })


def transaction_create(request):
    if request.method == 'POST':
        form = InventoryTransactionForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'تم تسجيل الحركة المخزنية بنجاح.')
                return redirect('inventory_transaction_list')
            except Exception as e:
                form.add_error(None, str(e))
    else:
        form = InventoryTransactionForm()

    return render(request, 'app_inventory/transaction_form.html', {
        'form': form,
        'page_title': 'إضافة حركة مخزنية',
    })


def recall_list(request):
    query = request.GET.get('q', '')
    recalls = RecallNotice.objects.select_related('item', 'lot').all().order_by('-notice_date', '-id')

    if query:
        recalls = recalls.filter(
            Q(item__item_name__icontains=query) |
            Q(lot__lot_number__icontains=query) |
            Q(recall_number__icontains=query)
        )

    return render(request, 'app_inventory/recall_list.html', {
        'recalls': recalls,
        'query': query,
    })


def recall_create(request):
    if request.method == 'POST':
        form = RecallNoticeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم إضافة إشعار السحب بنجاح.')
            return redirect('inventory_recall_list')
    else:
        form = RecallNoticeForm()

    return render(request, 'app_inventory/recall_form.html', {
        'form': form,
        'page_title': 'إضافة إشعار سحب',
    })


def item_lots_api(request, item_id):
    lots = InventoryLot.objects.filter(item_id=item_id).order_by('lot_number')
    data = [
        {
            'id': lot.id,
            'text': f'{lot.lot_number} ({lot.quantity})'
        }
        for lot in lots
    ]
    return JsonResponse({'lots': data})