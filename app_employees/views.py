from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    EmployeeForm,
    EmployeeCompensationForm,
    EmployeePenaltyForm,
    EmployeeBonusForm,
    EmployeeExpenseClaimForm,
    EmployeeAdvanceForm,
    EmployeeCommissionForm,
    EmployeePayrollForm,
)
from .models import (
    Employee,
    EmployeeCompensation,
    EmployeePenalty,
    EmployeeBonus,
    EmployeeExpenseClaim,
    EmployeeAdvance,
    EmployeeCommission,
    EmployeePayroll,
)


def employee_dashboard(request):
    total_employees = Employee.objects.count()
    active_employees = Employee.objects.filter(status='Active').count()
    sales_enabled = Employee.objects.filter(can_do_sales=True, status='Active').count()
    service_enabled = Employee.objects.filter(can_do_service=True, status='Active').count()

    recent_commissions = EmployeeCommission.objects.select_related('employee').order_by('-commission_date', '-id')[:10]
    recent_payrolls = EmployeePayroll.objects.select_related('employee').order_by('-year', '-month', '-id')[:10]

    return render(request, 'app_employees/employee_dashboard.html', {
        'total_employees': total_employees,
        'active_employees': active_employees,
        'sales_enabled': sales_enabled,
        'service_enabled': service_enabled,
        'recent_commissions': recent_commissions,
        'recent_payrolls': recent_payrolls,
    })


def employee_list(request):
    query = request.GET.get('q', '').strip()
    employees = Employee.objects.select_related('direct_manager').all().order_by('full_name')

    if query:
        employees = employees.filter(
            Q(employee_code__icontains=query) |
            Q(full_name__icontains=query) |
            Q(phone__icontains=query) |
            Q(job_title__icontains=query) |
            Q(department__icontains=query)
        )

    return render(request, 'app_employees/employee_list.html', {
        'employees': employees,
        'query': query,
    })


def employee_create(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            employee = form.save()
            messages.success(request, f'تم إضافة الموظف {employee.full_name} بنجاح.')
            return redirect('employee_list')
    else:
        form = EmployeeForm()

    return render(request, 'app_employees/employee_form.html', {
        'form': form,
        'page_title': 'إضافة موظف جديد',
    })


def employee_edit(request, employee_id):
    employee = get_object_or_404(Employee, pk=employee_id)

    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تعديل بيانات الموظف بنجاح.')
            return redirect('employee_list')
    else:
        form = EmployeeForm(instance=employee)

    return render(request, 'app_employees/employee_form.html', {
        'form': form,
        'page_title': f'تعديل الموظف: {employee.full_name}',
    })


def employee_detail(request, employee_id):
    employee = get_object_or_404(Employee, pk=employee_id)

    return render(request, 'app_employees/employee_detail.html', {
        'employee': employee,
        'compensation': getattr(employee, 'compensation', None),
        'penalties': employee.penalties.all()[:10],
        'bonuses': employee.bonuses.all()[:10],
        'expenses': employee.expense_claims.all()[:10],
        'advances': employee.advances.all()[:10],
        'commissions': employee.commissions.all()[:10],
        'payrolls': employee.payrolls.all()[:10],
    })


def compensation_list(request):
    rows = EmployeeCompensation.objects.select_related('employee').all().order_by('employee__full_name')
    return render(request, 'app_employees/compensation_list.html', {'rows': rows})


def compensation_create(request):
    if request.method == 'POST':
        form = EmployeeCompensationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم حفظ البيانات المالية بنجاح.')
            return redirect('compensation_list')
    else:
        form = EmployeeCompensationForm()

    return render(request, 'app_employees/simple_form.html', {
        'form': form,
        'page_title': 'إضافة بيانات مالية للموظف',
        'back_url_name': 'compensation_list',
    })


def penalty_list(request):
    rows = EmployeePenalty.objects.select_related('employee').all().order_by('-penalty_date', '-id')
    return render(request, 'app_employees/penalty_list.html', {'rows': rows})


def penalty_create(request):
    if request.method == 'POST':
        form = EmployeePenaltyForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تسجيل الجزاء بنجاح.')
            return redirect('penalty_list')
    else:
        form = EmployeePenaltyForm()

    return render(request, 'app_employees/simple_form.html', {
        'form': form,
        'page_title': 'إضافة جزاء',
        'back_url_name': 'penalty_list',
    })


def bonus_list(request):
    rows = EmployeeBonus.objects.select_related('employee').all().order_by('-bonus_date', '-id')
    return render(request, 'app_employees/bonus_list.html', {'rows': rows})


def bonus_create(request):
    if request.method == 'POST':
        form = EmployeeBonusForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تسجيل الحافز / المكافأة بنجاح.')
            return redirect('bonus_list')
    else:
        form = EmployeeBonusForm()

    return render(request, 'app_employees/simple_form.html', {
        'form': form,
        'page_title': 'إضافة حافز / مكافأة',
        'back_url_name': 'bonus_list',
    })


def expense_list(request):
    rows = EmployeeExpenseClaim.objects.select_related('employee').all().order_by('-expense_date', '-id')
    return render(request, 'app_employees/expense_list.html', {'rows': rows})


def expense_create(request):
    if request.method == 'POST':
        form = EmployeeExpenseClaimForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تسجيل المصروف بنجاح.')
            return redirect('expense_list')
    else:
        form = EmployeeExpenseClaimForm()

    return render(request, 'app_employees/simple_form.html', {
        'form': form,
        'page_title': 'إضافة مصروف مسترد',
        'back_url_name': 'expense_list',
    })


def advance_list(request):
    rows = EmployeeAdvance.objects.select_related('employee').all().order_by('-advance_date', '-id')
    return render(request, 'app_employees/advance_list.html', {'rows': rows})


def advance_create(request):
    if request.method == 'POST':
        form = EmployeeAdvanceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تسجيل السلفة بنجاح.')
            return redirect('advance_list')
    else:
        form = EmployeeAdvanceForm()

    return render(request, 'app_employees/simple_form.html', {
        'form': form,
        'page_title': 'إضافة سلفة',
        'back_url_name': 'advance_list',
    })


def commission_list(request):
    rows = EmployeeCommission.objects.select_related('employee', 'customer', 'invoice', 'quotation').all().order_by('-commission_date', '-id')
    return render(request, 'app_employees/commission_list.html', {'rows': rows})


def commission_create(request):
    if request.method == 'POST':
        form = EmployeeCommissionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تسجيل العمولة بنجاح.')
            return redirect('commission_list')
    else:
        form = EmployeeCommissionForm()

    return render(request, 'app_employees/simple_form.html', {
        'form': form,
        'page_title': 'إضافة عمولة',
        'back_url_name': 'commission_list',
    })


def payroll_list(request):
    rows = EmployeePayroll.objects.select_related('employee').all().order_by('-year', '-month', 'employee__full_name')
    return render(request, 'app_employees/payroll_list.html', {'rows': rows})


def payroll_create(request):
    if request.method == 'POST':
        form = EmployeePayrollForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم إنشاء مسير الراتب بنجاح.')
            return redirect('payroll_list')
    else:
        form = EmployeePayrollForm()

    return render(request, 'app_employees/simple_form.html', {
        'form': form,
        'page_title': 'إنشاء مسير راتب',
        'back_url_name': 'payroll_list',
    })