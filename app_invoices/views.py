from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.forms import modelformset_factory
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from app_inventory.models import InventoryItem, InventoryLot
from app_quotations.models import Quotation
from .forms import InvoiceForm, InvoiceItemForm
from .models import Invoice, InvoiceItem, InvoicePrintSettings


def invoice_list(request):
    query = request.GET.get('q', '')
    invoices = Invoice.objects.select_related('sales_owner', 'commission_owner').all().order_by('-id')

    if query:
        invoices = invoices.filter(
            Q(customer_name__icontains=query) |
            Q(id__icontains=query) |
            Q(sales_owner__full_name__icontains=query) |
            Q(commission_owner__full_name__icontains=query)
        )

    return render(request, 'app_invoices/invoice_list.html', {
        'invoices': invoices,
        'query': query,
    })


def invoice_create(request):
    InvoiceItemFormSet = modelformset_factory(
        InvoiceItem,
        form=InvoiceItemForm,
        extra=3,
        can_delete=True
    )

    if request.method == 'POST':
        invoice_form = InvoiceForm(request.POST)
        formset = InvoiceItemFormSet(request.POST, queryset=InvoiceItem.objects.none(), prefix='items')

        if invoice_form.is_valid() and formset.is_valid():
            invoice = invoice_form.save()

            has_items = False
            for form in formset:
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    if not form.cleaned_data.get('item'):
                        continue
                    item_obj = form.save(commit=False)
                    item_obj.invoice = invoice
                    item_obj.save()
                    has_items = True

            invoice.recalculate_totals()

            if not has_items:
                messages.warning(request, 'تم حفظ الفاتورة بدون بنود.')
            else:
                messages.success(request, 'تم حفظ الفاتورة بنجاح.')

            return redirect('invoice_detail', invoice_id=invoice.id)
    else:
        invoice_form = InvoiceForm(initial={
            'discount_percent': 0,
            'vat_percent': 14,
        })
        formset = InvoiceItemFormSet(queryset=InvoiceItem.objects.none(), prefix='items')

    return render(request, 'app_invoices/invoice_create_full.html', {
        'invoice_form': invoice_form,
        'formset': formset,
        'page_title': 'فاتورة جديدة',
        'is_edit': False,
        'invoice': None,
    })


def invoice_detail(request, invoice_id):
    invoice = get_object_or_404(Invoice, pk=invoice_id)

    InvoiceItemFormSet = modelformset_factory(
        InvoiceItem,
        form=InvoiceItemForm,
        extra=2,
        can_delete=True
    )

    if request.method == 'POST':
        if invoice.status == 'posted':
            messages.error(request, 'لا يمكن تعديل فاتورة تم ترحيلها.')
            return redirect('invoice_detail', invoice_id=invoice.id)

        if invoice.status == 'cancelled':
            messages.error(request, 'لا يمكن تعديل فاتورة ملغاة.')
            return redirect('invoice_detail', invoice_id=invoice.id)

        invoice_form = InvoiceForm(request.POST, instance=invoice)
        formset = InvoiceItemFormSet(request.POST, queryset=invoice.items.all(), prefix='items')

        if invoice_form.is_valid() and formset.is_valid():
            invoice = invoice_form.save()

            for obj in formset.deleted_objects:
                obj.delete()

            objects = formset.save(commit=False)
            for obj in objects:
                if not obj.item_id:
                    continue
                obj.invoice = invoice
                obj.save()

            invoice.recalculate_totals()
            messages.success(request, 'تم تحديث الفاتورة بنجاح.')
            return redirect('invoice_detail', invoice_id=invoice.id)
    else:
        invoice_form = InvoiceForm(instance=invoice)
        formset = InvoiceItemFormSet(queryset=invoice.items.all(), prefix='items')

    return render(request, 'app_invoices/invoice_create_full.html', {
        'invoice_form': invoice_form,
        'formset': formset,
        'page_title': f'فاتورة رقم {invoice.id}',
        'is_edit': True,
        'invoice': invoice,
    })


@transaction.atomic
def create_invoice_from_quotation(request, quotation_id):
    quotation = get_object_or_404(Quotation, pk=quotation_id)

    if hasattr(quotation, 'invoice'):
        messages.warning(request, 'تم إنشاء فاتورة لهذا العرض بالفعل.')
        return redirect('invoice_detail', invoice_id=quotation.invoice.id)

    invoice = Invoice.objects.create(
        quotation=quotation,
        customer_name=quotation.display_customer_name,
        sales_owner=quotation.sales_owner,
        commission_owner=quotation.commission_owner,
        discount_percent=quotation.discount_percent,
        vat_percent=quotation.vat_percent,
        notes=quotation.notes,
    )

    created_items = 0
    skipped_items = 0

    for q_item in quotation.items.all():
        if not q_item.inventory_item:
            skipped_items += 1
            continue

        InvoiceItem.objects.create(
            invoice=invoice,
            item=q_item.inventory_item,
            quantity=q_item.quantity,
            price=q_item.price,
            description=q_item.description,
        )
        created_items += 1

    invoice.recalculate_totals()

    quotation.status = 'Converted'
    quotation.save(update_fields=['status'])

    if created_items == 0:
        messages.warning(
            request,
            'تم إنشاء الفاتورة، لكن لم تتم إضافة بنود لأن بنود عرض السعر غير مرتبطة بأصناف مخزنية.'
        )
    elif skipped_items > 0:
        messages.warning(
            request,
            f'تم إنشاء الفاتورة بنجاح. تم إضافة {created_items} بند وتخطي {skipped_items} بند غير مرتبط بالمخزن.'
        )
    else:
        messages.success(request, 'تم إنشاء الفاتورة من عرض السعر بنجاح.')

    return redirect('invoice_detail', invoice_id=invoice.id)


def post_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, pk=invoice_id)

    try:
        invoice.post_invoice()
        messages.success(request, 'تم ترحيل الفاتورة وخصم الكميات من المخزن وإنشاء العمولة بنجاح.')
    except Exception as e:
        messages.error(request, str(e))

    return redirect('invoice_detail', invoice_id=invoice.id)


def cancel_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, pk=invoice_id)

    try:
        invoice.cancel_invoice()
        messages.success(request, 'تم إلغاء الفاتورة بنجاح.')
    except Exception as e:
        messages.error(request, str(e))

    return redirect('invoice_detail', invoice_id=invoice.id)


def invoice_print(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    print_settings = InvoicePrintSettings.objects.first()

    return render(request, 'app_invoices/invoice_print.html', {
        'invoice': invoice,
        'print_settings': print_settings,
    })


def item_meta(request, item_id):
    item = get_object_or_404(InventoryItem, pk=item_id)

    lots = InventoryLot.objects.filter(item=item).order_by('id')
    lots_data = [
        {
            'id': lot.id,
            'text': f'{lot.lot_number} ({lot.quantity})',
            'quantity': str(lot.quantity),
        }
        for lot in lots
    ]

    return JsonResponse({
        'sale_price': str(item.sale_price),
        'lots': lots_data,
    })