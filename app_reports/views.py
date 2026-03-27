from decimal import Decimal

from django.db.models import Sum, Count
from django.shortcuts import render

from app_invoices.models import Invoice
from app_employees.models import EmployeeCommission
from app_quotations.models import Quotation


def sales_dashboard(request):
    quotations = Quotation.objects.select_related('customer', 'sales_owner', 'commission_owner').all()
    invoices = Invoice.objects.select_related('sales_owner', 'commission_owner').all()

    total_quotations = quotations.count()
    total_invoices = invoices.count()

    converted_quotations = quotations.filter(status='Converted').count()
    draft_quotations = quotations.filter(status='Draft').count()

    posted_invoices_qs = invoices.filter(status='posted')
    posted_invoices = posted_invoices_qs.count()
    draft_invoices = invoices.filter(status='draft').count()
    cancelled_invoices = invoices.filter(status='cancelled').count()

    total_sales = posted_invoices_qs.aggregate(
        total=Sum('total_after_vat')
    )['total'] or Decimal('0')

    avg_invoice = Decimal('0')
    if posted_invoices > 0:
        avg_invoice = total_sales / posted_invoices

    total_commissions = EmployeeCommission.objects.filter(
        status__in=['Approved', 'Paid']
    ).aggregate(
        total=Sum('commission_amount')
    )['total'] or Decimal('0')

    recent_quotations = quotations.order_by('-id')[:10]
    recent_invoices = invoices.order_by('-id')[:10]

    top_sales_people = (
        posted_invoices_qs.filter(sales_owner__isnull=False)
        .values('sales_owner__full_name')
        .annotate(
            invoices_count=Count('id'),
            sales_total=Sum('total_after_vat')
        )
        .order_by('-sales_total')[:10]
    )

    return render(request, 'app_reports/sales_dashboard.html', {
        'total_quotations': total_quotations,
        'total_invoices': total_invoices,
        'converted_quotations': converted_quotations,
        'draft_quotations': draft_quotations,
        'posted_invoices': posted_invoices,
        'draft_invoices': draft_invoices,
        'cancelled_invoices': cancelled_invoices,
        'total_sales': total_sales,
        'avg_invoice': avg_invoice,
        'total_commissions': total_commissions,
        'recent_quotations': recent_quotations,
        'recent_invoices': recent_invoices,
        'top_sales_people': top_sales_people,
    })


def commission_report(request):
    rows = EmployeeCommission.objects.select_related(
        'employee',
        'customer',
        'quotation',
        'invoice'
    ).all().order_by('-commission_date', '-id')

    total_commissions = rows.aggregate(
        total=Sum('commission_amount')
    )['total'] or Decimal('0')

    approved_total = rows.filter(status='Approved').aggregate(
        total=Sum('commission_amount')
    )['total'] or Decimal('0')

    paid_total = rows.filter(status='Paid').aggregate(
        total=Sum('commission_amount')
    )['total'] or Decimal('0')

    return render(request, 'app_reports/commission_report.html', {
        'rows': rows,
        'total_commissions': total_commissions,
        'approved_total': approved_total,
        'paid_total': paid_total,
    })