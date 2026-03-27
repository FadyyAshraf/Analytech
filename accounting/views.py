from decimal import Decimal

from django.contrib import messages
from django.db.models import Q
from django.forms import modelformset_factory
from django.shortcuts import get_object_or_404, redirect, render

from customers.models import Customer
from .forms import (
    AccountForm,
    JournalEntryForm,
    JournalEntryLineForm,
    ReceiptVoucherForm,
    PaymentVoucherForm,
)
from .models import (
    Account,
    JournalEntry,
    JournalEntryLine,
    ReceiptVoucher,
    PaymentVoucher,
)


def accounting_dashboard(request):
    accounts_count = Account.objects.count()
    journal_count = JournalEntry.objects.count()
    posted_journal_count = JournalEntry.objects.filter(status='Posted').count()
    draft_journal_count = JournalEntry.objects.filter(status='Draft').count()

    receipts_total = sum((x.amount for x in ReceiptVoucher.objects.all()), Decimal('0'))
    payments_total = sum((x.amount for x in PaymentVoucher.objects.all()), Decimal('0'))

    recent_entries = JournalEntry.objects.all().order_by('-entry_date', '-id')[:10]
    recent_receipts = ReceiptVoucher.objects.select_related('customer').all().order_by('-voucher_date', '-id')[:10]

    return render(request, 'accounting/accounting_dashboard.html', {
        'accounts_count': accounts_count,
        'journal_count': journal_count,
        'posted_journal_count': posted_journal_count,
        'draft_journal_count': draft_journal_count,
        'receipts_total': receipts_total,
        'payments_total': payments_total,
        'recent_entries': recent_entries,
        'recent_receipts': recent_receipts,
    })


def account_list(request):
    query = request.GET.get('q', '')
    accounts = Account.objects.select_related('parent').all().order_by('code')

    if query:
        accounts = accounts.filter(
            Q(code__icontains=query) |
            Q(name__icontains=query) |
            Q(account_type__icontains=query)
        )

    return render(request, 'accounting/account_list.html', {
        'accounts': accounts,
        'query': query,
    })


def account_create(request):
    if request.method == 'POST':
        form = AccountForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم إضافة الحساب بنجاح.')
            return redirect('account_list')
    else:
        form = AccountForm()

    return render(request, 'accounting/account_form.html', {
        'form': form,
        'page_title': 'إضافة حساب جديد',
    })


def account_edit(request, account_id):
    account = get_object_or_404(Account, pk=account_id)

    if request.method == 'POST':
        form = AccountForm(request.POST, instance=account)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تعديل الحساب بنجاح.')
            return redirect('account_list')
    else:
        form = AccountForm(instance=account)

    return render(request, 'accounting/account_form.html', {
        'form': form,
        'page_title': f'تعديل الحساب: {account.name}',
    })


def journal_entry_list(request):
    query = request.GET.get('q', '')
    entries = JournalEntry.objects.all().order_by('-entry_date', '-id')

    if query:
        entries = entries.filter(
            Q(description__icontains=query) |
            Q(reference__icontains=query) |
            Q(status__icontains=query)
        )

    return render(request, 'accounting/journal_entry_list.html', {
        'entries': entries,
        'query': query,
    })


def journal_entry_create(request):
    LineFormSet = modelformset_factory(
        JournalEntryLine,
        form=JournalEntryLineForm,
        extra=2,
        can_delete=True
    )

    if request.method == 'POST':
        entry_form = JournalEntryForm(request.POST)
        formset = LineFormSet(request.POST, queryset=JournalEntryLine.objects.none(), prefix='lines')

        if entry_form.is_valid() and formset.is_valid():
            entry = entry_form.save()

            has_lines = False
            for form in formset:
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    line = form.save(commit=False)
                    line.entry = entry
                    line.save()
                    has_lines = True

            if not has_lines:
                messages.warning(request, 'تم حفظ القيد بدون سطور.')
            else:
                messages.success(request, 'تم حفظ القيد بنجاح.')

            return redirect('journal_entry_detail', entry_id=entry.id)
    else:
        entry_form = JournalEntryForm(initial={'status': 'Draft'})
        formset = LineFormSet(queryset=JournalEntryLine.objects.none(), prefix='lines')

    return render(request, 'accounting/journal_entry_form.html', {
        'entry_form': entry_form,
        'formset': formset,
        'page_title': 'قيد يومية جديد',
        'entry': None,
        'is_edit': False,
    })


def journal_entry_detail(request, entry_id):
    entry = get_object_or_404(JournalEntry, pk=entry_id)

    LineFormSet = modelformset_factory(
        JournalEntryLine,
        form=JournalEntryLineForm,
        extra=1,
        can_delete=True
    )

    if request.method == 'POST':
        if entry.status == 'Posted':
            messages.error(request, 'لا يمكن تعديل قيد تم ترحيله.')
            return redirect('journal_entry_detail', entry_id=entry.id)

        if entry.status == 'Cancelled':
            messages.error(request, 'لا يمكن تعديل قيد ملغي.')
            return redirect('journal_entry_detail', entry_id=entry.id)

        entry_form = JournalEntryForm(request.POST, instance=entry)
        formset = LineFormSet(request.POST, queryset=entry.lines.all(), prefix='lines')

        if entry_form.is_valid() and formset.is_valid():
            entry = entry_form.save()

            for obj in formset.deleted_objects:
                obj.delete()

            objects = formset.save(commit=False)
            for obj in objects:
                obj.entry = entry
                obj.save()

            messages.success(request, 'تم تحديث القيد بنجاح.')
            return redirect('journal_entry_detail', entry_id=entry.id)
    else:
        entry_form = JournalEntryForm(instance=entry)
        formset = LineFormSet(queryset=entry.lines.all(), prefix='lines')

    return render(request, 'accounting/journal_entry_form.html', {
        'entry_form': entry_form,
        'formset': formset,
        'page_title': f'قيد رقم {entry.id}',
        'entry': entry,
        'is_edit': True,
    })


def journal_entry_post(request, entry_id):
    entry = get_object_or_404(JournalEntry, pk=entry_id)

    try:
        entry.post()
        messages.success(request, 'تم ترحيل القيد بنجاح.')
    except Exception as e:
        messages.error(request, str(e))

    return redirect('journal_entry_detail', entry_id=entry.id)


def journal_entry_cancel(request, entry_id):
    entry = get_object_or_404(JournalEntry, pk=entry_id)

    try:
        entry.cancel()
        messages.success(request, 'تم إلغاء القيد بنجاح.')
    except Exception as e:
        messages.error(request, str(e))

    return redirect('journal_entry_detail', entry_id=entry.id)


def receipt_voucher_list(request):
    query = request.GET.get('q', '')
    vouchers = ReceiptVoucher.objects.select_related(
        'customer',
        'debit_account',
        'credit_account',
        'journal_entry'
    ).all().order_by('-voucher_date', '-id')

    if query:
        vouchers = vouchers.filter(
            Q(payer_name__icontains=query) |
            Q(customer__name__icontains=query) |
            Q(reference__icontains=query) |
            Q(description__icontains=query)
        )

    return render(request, 'accounting/receipt_voucher_list.html', {
        'vouchers': vouchers,
        'query': query,
    })


def receipt_voucher_create(request):
    if request.method == 'POST':
        form = ReceiptVoucherForm(request.POST)
        if form.is_valid():
            voucher = form.save()
            try:
                voucher.create_journal_entry()
                messages.success(request, 'تم إنشاء سند القبض والقيد المحاسبي بنجاح.')
            except Exception as e:
                messages.warning(request, f'تم حفظ السند لكن لم يُنشأ القيد: {e}')
            return redirect('receipt_voucher_list')
    else:
        form = ReceiptVoucherForm(initial={'debit_account': Account.objects.filter(code='1000').first()})

    return render(request, 'accounting/receipt_voucher_form.html', {
        'form': form,
        'page_title': 'سند قبض جديد',
        'is_edit': False,
        'voucher': None,
    })


def receipt_voucher_edit(request, voucher_id):
    voucher = get_object_or_404(ReceiptVoucher, pk=voucher_id)

    if voucher.journal_entry and voucher.journal_entry.status == 'Posted':
        messages.error(request, 'لا يمكن تعديل سند قبض له قيد مُرحل. قم بإلغاء القيد أولًا.')
        return redirect('receipt_voucher_list')

    if request.method == 'POST':
        form = ReceiptVoucherForm(request.POST, instance=voucher)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تعديل سند القبض بنجاح.')
            return redirect('receipt_voucher_list')
    else:
        form = ReceiptVoucherForm(instance=voucher)

    return render(request, 'accounting/receipt_voucher_form.html', {
        'form': form,
        'page_title': f'تعديل سند قبض رقم {voucher.id}',
        'is_edit': True,
        'voucher': voucher,
    })


def receipt_voucher_delete(request, voucher_id):
    voucher = get_object_or_404(ReceiptVoucher, pk=voucher_id)

    if voucher.journal_entry and voucher.journal_entry.status == 'Posted':
        messages.error(request, 'لا يمكن حذف سند قبض له قيد مُرحل. قم بإلغاء القيد أولًا.')
        return redirect('receipt_voucher_list')

    if request.method == 'POST':
        if voucher.journal_entry:
            voucher.journal_entry.delete()
        voucher.delete()
        messages.success(request, 'تم حذف سند القبض بنجاح.')
        return redirect('receipt_voucher_list')

    return render(request, 'accounting/receipt_voucher_delete.html', {
        'voucher': voucher,
    })


def payment_voucher_list(request):
    query = request.GET.get('q', '')
    vouchers = PaymentVoucher.objects.select_related(
        'debit_account',
        'credit_account',
        'journal_entry'
    ).all().order_by('-voucher_date', '-id')

    if query:
        vouchers = vouchers.filter(
            Q(payee_name__icontains=query) |
            Q(reference__icontains=query) |
            Q(description__icontains=query)
        )

    return render(request, 'accounting/payment_voucher_list.html', {
        'vouchers': vouchers,
        'query': query,
    })


def payment_voucher_create(request):
    if request.method == 'POST':
        form = PaymentVoucherForm(request.POST)
        if form.is_valid():
            voucher = form.save()
            try:
                voucher.create_journal_entry()
                messages.success(request, 'تم إنشاء سند الصرف والقيد المحاسبي بنجاح.')
            except Exception as e:
                messages.warning(request, f'تم حفظ السند لكن لم يُنشأ القيد: {e}')
            return redirect('payment_voucher_list')
    else:
        form = PaymentVoucherForm()

    return render(request, 'accounting/payment_voucher_form.html', {
        'form': form,
        'page_title': 'سند صرف جديد',
        'is_edit': False,
        'voucher': None,
    })


def payment_voucher_edit(request, voucher_id):
    voucher = get_object_or_404(PaymentVoucher, pk=voucher_id)

    if voucher.journal_entry and voucher.journal_entry.status == 'Posted':
        messages.error(request, 'لا يمكن تعديل سند صرف له قيد مُرحل. قم بإلغاء القيد أولًا.')
        return redirect('payment_voucher_list')

    if request.method == 'POST':
        form = PaymentVoucherForm(request.POST, instance=voucher)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تعديل سند الصرف بنجاح.')
            return redirect('payment_voucher_list')
    else:
        form = PaymentVoucherForm(instance=voucher)

    return render(request, 'accounting/payment_voucher_form.html', {
        'form': form,
        'page_title': f'تعديل سند صرف رقم {voucher.id}',
        'is_edit': True,
        'voucher': voucher,
    })


def payment_voucher_delete(request, voucher_id):
    voucher = get_object_or_404(PaymentVoucher, pk=voucher_id)

    if voucher.journal_entry and voucher.journal_entry.status == 'Posted':
        messages.error(request, 'لا يمكن حذف سند صرف له قيد مُرحل. قم بإلغاء القيد أولًا.')
        return redirect('payment_voucher_list')

    if request.method == 'POST':
        if voucher.journal_entry:
            voucher.journal_entry.delete()
        voucher.delete()
        messages.success(request, 'تم حذف سند الصرف بنجاح.')
        return redirect('payment_voucher_list')

    return render(request, 'accounting/payment_voucher_delete.html', {
        'voucher': voucher,
    })


def customer_statement(request):
    customer_id = request.GET.get('customer')

    selected_customer = None
    selected_account = None
    lines = []
    balance = Decimal('0')

    customers = Customer.objects.select_related('account').all().order_by('name')

    if customer_id:
        selected_customer = get_object_or_404(Customer.objects.select_related('account'), pk=customer_id)

        if not selected_customer.account_id:
            selected_customer.create_account_if_missing()
            selected_customer.refresh_from_db()

        selected_account = selected_customer.account

        if selected_account:
            entry_lines = JournalEntryLine.objects.filter(
                account=selected_account,
                entry__status='Posted'
            ).select_related('entry').order_by('entry__entry_date', 'id')

            running_balance = Decimal('0')
            result = []

            for line in entry_lines:
                running_balance += line.debit - line.credit
                result.append({
                    'date': line.entry.entry_date,
                    'description': line.entry.description,
                    'reference': line.entry.reference,
                    'debit': line.debit,
                    'credit': line.credit,
                    'balance': running_balance,
                })

            lines = result
            balance = running_balance

    return render(request, 'accounting/customer_statement.html', {
        'customers': customers,
        'selected_customer': selected_customer,
        'selected_account': selected_account,
        'lines': lines,
        'balance': balance,
    })


def account_ledger(request):
    account_id = request.GET.get('account')

    selected_account = None
    lines = []
    balance = Decimal('0')

    accounts = Account.objects.all().order_by('code')

    if account_id:
        selected_account = get_object_or_404(Account, pk=account_id)

        entry_lines = JournalEntryLine.objects.filter(
            account=selected_account,
            entry__status='Posted'
        ).select_related('entry').order_by('entry__entry_date', 'id')

        running_balance = Decimal('0')
        result = []

        for line in entry_lines:
            running_balance += line.debit - line.credit
            result.append({
                'date': line.entry.entry_date,
                'description': line.entry.description,
                'reference': line.entry.reference,
                'debit': line.debit,
                'credit': line.credit,
                'balance': running_balance,
            })

        lines = result
        balance = running_balance

    return render(request, 'accounting/account_ledger.html', {
        'accounts': accounts,
        'selected_account': selected_account,
        'lines': lines,
        'balance': balance,
    })


def trial_balance_report(request):
    accounts = Account.objects.all().order_by('code')
    rows = []
    total_debit = Decimal('0')
    total_credit = Decimal('0')

    for account in accounts:
        debit = account.current_debit
        credit = account.current_credit

        if debit == 0 and credit == 0:
            continue

        rows.append({
            'account': account,
            'debit': debit,
            'credit': credit,
            'balance': debit - credit,
        })

        total_debit += debit
        total_credit += credit

    return render(request, 'accounting/trial_balance.html', {
        'rows': rows,
        'total_debit': total_debit,
        'total_credit': total_credit,
    })


def profit_loss_report(request):
    revenue_accounts = Account.objects.filter(account_type='Revenue').order_by('code')
    expense_accounts = Account.objects.filter(account_type='Expense').order_by('code')

    revenue_rows = []
    expense_rows = []

    total_revenue = Decimal('0')
    total_expense = Decimal('0')

    for account in revenue_accounts:
        amount = account.current_credit - account.current_debit
        if amount != 0:
            revenue_rows.append({'account': account, 'amount': amount})
            total_revenue += amount

    for account in expense_accounts:
        amount = account.current_debit - account.current_credit
        if amount != 0:
            expense_rows.append({'account': account, 'amount': amount})
            total_expense += amount

    net_profit = total_revenue - total_expense

    return render(request, 'accounting/profit_loss.html', {
        'revenue_rows': revenue_rows,
        'expense_rows': expense_rows,
        'total_revenue': total_revenue,
        'total_expense': total_expense,
        'net_profit': net_profit,
    })