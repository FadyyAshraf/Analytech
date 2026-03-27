from django.contrib import messages
from django.db.models import Q
from django.forms import modelformset_factory
from django.shortcuts import get_object_or_404, redirect, render

from app_maintenance.models import MaintenanceVisit
from .forms import QuotationForm, QuotationItemForm
from .models import Quotation, QuotationItem


def quotation_list(request):
    query = request.GET.get('q', '').strip()
    quotations = Quotation.objects.select_related(
        'customer',
        'device',
        'sales_owner',
        'commission_owner'
    ).all().order_by('-id')

    if query:
        quotations = quotations.filter(
            Q(customer__name__icontains=query) |
            Q(customer_name_manual__icontains=query) |
            Q(reference__icontains=query) |
            Q(subject__icontains=query) |
            Q(sales_owner__full_name__icontains=query) |
            Q(commission_owner__full_name__icontains=query)
        )

    return render(request, 'quotations/quotation_list.html', {
        'quotations': quotations,
        'query': query,
    })


def quotation_create(request):
    ItemFormSet = modelformset_factory(
        QuotationItem,
        form=QuotationItemForm,
        extra=1,
        can_delete=True
    )

    if request.method == 'POST':
        quotation_form = QuotationForm(request.POST)
        formset = ItemFormSet(
            request.POST,
            queryset=QuotationItem.objects.none(),
            prefix='items'
        )

        if quotation_form.is_valid() and formset.is_valid():
            quotation = quotation_form.save()

            has_items = False
            for form in formset:
                if not form.cleaned_data:
                    continue
                if form.cleaned_data.get('DELETE', False):
                    continue

                obj = form.save(commit=False)
                obj.quotation = quotation
                obj.save()
                has_items = True

            quotation.recalculate_totals()

            if has_items:
                messages.success(request, f'تم حفظ عرض السعر رقم {quotation.id} بنجاح.')
            else:
                messages.warning(request, f'تم حفظ عرض السعر رقم {quotation.id} بدون بنود.')

            return redirect('quotation_list')

    else:
        quotation_form = QuotationForm(initial={
            'quotation_type': 'Mixed',
            'status': 'Draft',
            'discount_percent': 0,
            'vat_percent': 14,
        })
        formset = ItemFormSet(
            queryset=QuotationItem.objects.none(),
            prefix='items'
        )

    return render(request, 'quotations/quotation_form.html', {
        'quotation_form': quotation_form,
        'formset': formset,
        'page_title': 'عرض سعر جديد',
        'quotation': None,
        'is_edit': False,
    })


def quotation_detail(request, quotation_id):
    quotation = get_object_or_404(Quotation, pk=quotation_id)

    ItemFormSet = modelformset_factory(
        QuotationItem,
        form=QuotationItemForm,
        extra=1,
        can_delete=True
    )

    if request.method == 'POST':
        quotation_form = QuotationForm(request.POST, instance=quotation)
        formset = ItemFormSet(
            request.POST,
            queryset=quotation.items.all(),
            prefix='items'
        )

        if quotation_form.is_valid() and formset.is_valid():
            quotation = quotation_form.save()

            for obj in formset.deleted_objects:
                obj.delete()

            objects = formset.save(commit=False)
            for obj in objects:
                obj.quotation = quotation
                obj.save()

            quotation.recalculate_totals()
            messages.success(request, f'تم تحديث عرض السعر رقم {quotation.id} بنجاح.')
            return redirect('quotation_list')

    else:
        quotation_form = QuotationForm(instance=quotation)
        formset = ItemFormSet(
            queryset=quotation.items.all(),
            prefix='items'
        )

    return render(request, 'quotations/quotation_form.html', {
        'quotation_form': quotation_form,
        'formset': formset,
        'page_title': f'عرض سعر رقم {quotation.id}',
        'quotation': quotation,
        'is_edit': True,
    })


def quotation_print(request, quotation_id):
    quotation = get_object_or_404(Quotation, pk=quotation_id)
    print_settings = None

    try:
        from app_invoices.models import InvoicePrintSettings
        print_settings = InvoicePrintSettings.objects.first()
    except Exception:
        print_settings = None

    return render(request, 'quotations/quotation_print.html', {
        'quotation': quotation,
        'print_settings': print_settings,
    })


def quotation_from_visit(request, visit_id):
    visit = get_object_or_404(MaintenanceVisit, pk=visit_id)

    quotation = Quotation.objects.create(
        customer=visit.customer,
        device=visit.device,
        sales_owner=visit.engineer if visit.engineer and visit.engineer.can_do_sales else None,
        commission_owner=visit.engineer if visit.engineer and visit.engineer.can_do_sales else None,
        quotation_type='Mixed' if visit.needs_spare_parts else 'Service',
        status='Draft',
        maintenance_request=visit.request,
        maintenance_visit=visit,
        subject=f'عرض سعر لزيارة الصيانة رقم {visit.id}',
        reference=f'MV-{visit.id}',
        notes=visit.final_result or '',
    )

    requirements = visit.requirements.all()
    for req in requirements:
        QuotationItem.objects.create(
            quotation=quotation,
            item_type='Spare Part',
            inventory_item=req.item,
            maintenance_requirement=req,
            description=req.item.item_name,
            quantity=req.quantity,
            price=req.item.sale_price if hasattr(req.item, 'sale_price') else 0,
        )

    quotation.recalculate_totals()
    messages.success(request, f'تم إنشاء عرض السعر رقم {quotation.id} من زيارة الصيانة.')
    return redirect('quotation_detail', quotation_id=quotation.id)