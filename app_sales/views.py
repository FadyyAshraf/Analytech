from django.contrib import messages
from django.forms import modelformset_factory
from django.shortcuts import get_object_or_404, redirect, render

from app_invoices.models import Invoice, InvoiceItem
from .forms import SalesOrderForm, SalesOrderItemForm
from .models import SalesOrder, SalesOrderItem


def sales_order_list(request):
    orders = SalesOrder.objects.select_related(
        'customer',
        'sales_owner',
        'invoice',
        'internal_delivery_employee'
    ).all().order_by('-id')

    return render(request, 'app_sales/order_list.html', {
        'orders': orders,
    })


def sales_order_create(request):
    ItemFormSet = modelformset_factory(
        SalesOrderItem,
        form=SalesOrderItemForm,
        extra=3,
        can_delete=True
    )

    if request.method == 'POST':
        order_form = SalesOrderForm(request.POST)
        formset = ItemFormSet(request.POST, queryset=SalesOrderItem.objects.none(), prefix='items')

        if order_form.is_valid() and formset.is_valid():
            order = order_form.save()

            has_items = False
            for form in formset:
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    if not form.cleaned_data.get('item'):
                        continue
                    obj = form.save(commit=False)
                    obj.order = order
                    obj.save()
                    has_items = True

            if has_items:
                order.recalculate_totals()
                messages.success(request, f'تم حفظ طلب البيع رقم {order.id} بنجاح.')
            else:
                messages.warning(request, 'تم حفظ الطلب بدون بنود.')

            return redirect('sales_order_detail', order_id=order.id)
    else:
        order_form = SalesOrderForm()
        formset = ItemFormSet(queryset=SalesOrderItem.objects.none(), prefix='items')

    return render(request, 'app_sales/order_form.html', {
        'order_form': order_form,
        'formset': formset,
        'page_title': 'طلب بيع جديد',
        'order': None,
        'is_edit': False,
    })


def sales_order_detail(request, order_id):
    order = get_object_or_404(SalesOrder, pk=order_id)

    ItemFormSet = modelformset_factory(
        SalesOrderItem,
        form=SalesOrderItemForm,
        extra=2,
        can_delete=True
    )

    if request.method == 'POST':
        if order.status in ['Released', 'Shipped', 'Delivered', 'Closed', 'Cancelled']:
            messages.error(request, 'لا يمكن تعديل الطلب بعد الصرف أو الشحن أو الإغلاق.')
            return redirect('sales_order_detail', order_id=order.id)

        order_form = SalesOrderForm(request.POST, instance=order)
        formset = ItemFormSet(request.POST, queryset=order.items.all(), prefix='items')

        if order_form.is_valid() and formset.is_valid():
            order = order_form.save()

            for obj in formset.deleted_objects:
                obj.delete()

            objects = formset.save(commit=False)
            for obj in objects:
                if not obj.item_id:
                    continue
                obj.order = order
                obj.save()

            order.recalculate_totals()
            messages.success(request, 'تم تحديث طلب البيع بنجاح.')
            return redirect('sales_order_detail', order_id=order.id)
    else:
        order_form = SalesOrderForm(instance=order)
        formset = ItemFormSet(queryset=order.items.all(), prefix='items')

    return render(request, 'app_sales/order_detail.html', {
        'order_form': order_form,
        'formset': formset,
        'page_title': f'طلب بيع رقم {order.id}',
        'order': order,
        'is_edit': True,
    })


def sales_order_confirm(request, order_id):
    order = get_object_or_404(SalesOrder, pk=order_id)
    try:
        order.mark_confirmed()
        messages.success(request, 'تم اعتماد طلب البيع بنجاح.')
    except Exception as e:
        messages.error(request, str(e))
    return redirect('sales_order_detail', order_id=order.id)


def sales_order_release(request, order_id):
    order = get_object_or_404(SalesOrder, pk=order_id)
    try:
        order.release_from_inventory()
        messages.success(request, 'تم صرف الطلب من المخزن بنجاح.')
    except Exception as e:
        messages.error(request, str(e))
    return redirect('sales_order_detail', order_id=order.id)


def sales_order_ship(request, order_id):
    order = get_object_or_404(SalesOrder, pk=order_id)
    try:
        order.mark_shipped()
        messages.success(request, 'تم تسجيل خروج الطلب للشحن/التوصيل.')
    except Exception as e:
        messages.error(request, str(e))
    return redirect('sales_order_detail', order_id=order.id)


def sales_order_deliver(request, order_id):
    order = get_object_or_404(SalesOrder, pk=order_id)
    try:
        order.mark_delivered()
        messages.success(request, 'تم تأكيد استلام العميل للطلب.')
    except Exception as e:
        messages.error(request, str(e))
    return redirect('sales_order_detail', order_id=order.id)


def sales_order_close(request, order_id):
    order = get_object_or_404(SalesOrder, pk=order_id)
    try:
        order.close_order()
        messages.success(request, 'تم إغلاق طلب البيع.')
    except Exception as e:
        messages.error(request, str(e))
    return redirect('sales_order_detail', order_id=order.id)


def create_invoice_from_sales_order(request, order_id):
    order = get_object_or_404(SalesOrder, pk=order_id)

    if order.invoice_id:
        messages.warning(request, 'تم إنشاء فاتورة لهذا الطلب بالفعل.')
        return redirect('invoice_detail', invoice_id=order.invoice.id)

    invoice = Invoice.objects.create(
        customer_name=order.customer.name,
        sales_owner=order.sales_owner,
        commission_owner=order.sales_owner,
        notes=f'فاتورة ناتجة من طلب بيع رقم {order.id}',
    )

    created_items = 0
    for row in order.items.select_related('item', 'lot').all():
        InvoiceItem.objects.create(
            invoice=invoice,
            item=row.item,
            lot=row.lot,
            description=row.description,
            quantity=row.quantity,
            price=row.price,
        )
        created_items += 1

    invoice.recalculate_totals()

    order.invoice = invoice
    order.save(update_fields=['invoice'])

    messages.success(request, f'تم إنشاء فاتورة رقم {invoice.id} من طلب البيع.')
    return redirect('invoice_detail', invoice_id=invoice.id)