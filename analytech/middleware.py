from django.conf import settings
from django.shortcuts import redirect, render


class RequireLoginAndPermissionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        if self.is_exempt_path(path):
            return self.get_response(request)

        if not request.user.is_authenticated:
            return redirect(f"{settings.LOGIN_URL}?next={path}")

        if request.user.is_superuser:
            return self.get_response(request)

        required_permissions = self.get_required_permissions(path)

        if not required_permissions:
            return self.get_response(request)

        if any(request.user.has_perm(perm) for perm in required_permissions):
            return self.get_response(request)

        return render(request, '403.html', status=403)

    def is_exempt_path(self, path):
        exempt_prefixes = [
            settings.LOGIN_URL,
            settings.LOGOUT_REDIRECT_URL,
            '/logout/',
            '/admin/',
            '/static/',
            '/media/',
            '/favicon.ico',
        ]
        return any(path.startswith(prefix) for prefix in exempt_prefixes)

    def detect_action(self, path):
        if '/delete/' in path:
            return 'delete'

        add_markers = ['/create/', '/new/']
        if any(marker in path for marker in add_markers):
            return 'add'

        change_markers = [
            '/edit/',
            '/post/',
            '/cancel/',
            '/confirm/',
            '/release/',
            '/ship/',
            '/deliver/',
            '/close/',
        ]
        if any(marker in path for marker in change_markers):
            return 'change'

        return 'view'

    def build_permissions(self, action, models_list):
        return [f'{app_label}.{action}_{model_name}' for app_label, model_name in models_list]

    def get_required_permissions(self, path):
        action = self.detect_action(path)

        permission_map = [
            ('/customers/', [('customers', 'customer')]),
            ('/devices/', [('app_devices', 'device')]),
            ('/employees/', [('app_employees', 'employee')]),

            ('/sales-orders/', [('app_sales', 'salesorder')]),
            ('/quotations/', [('app_quotations', 'quotation')]),
            ('/invoices/', [('app_invoices', 'invoice')]),

            ('/reports/sales/', [
                ('app_sales', 'salesorder'),
                ('app_quotations', 'quotation'),
                ('app_invoices', 'invoice'),
            ]),
            ('/reports/commissions/', [('app_employees', 'employeecommission')]),

            ('/maintenance/requests/', [('app_maintenance', 'maintenancerequest')]),
            ('/maintenance/plans/', [('app_maintenance', 'preventivemaintenanceplan')]),
            ('/maintenance/visits/', [('app_maintenance', 'maintenancevisit')]),
            ('/maintenance/reports/', [
                ('app_maintenance', 'maintenancerequest'),
                ('app_maintenance', 'maintenancevisit'),
                ('app_maintenance', 'preventivemaintenanceplan'),
            ]),

            ('/inventory/items/', [('app_inventory', 'inventoryitem')]),
            ('/inventory/lots/', [('app_inventory', 'inventorylot')]),
            ('/inventory/transactions/', [('app_inventory', 'inventorytransaction')]),
            ('/inventory/recalls/', [('app_inventory', 'recallnotice')]),
            ('/inventory/', [('app_inventory', 'inventoryitem')]),

            ('/accounting/accounts/', [('accounting', 'account')]),
            ('/accounting/journal/', [('accounting', 'journalentry')]),
            ('/accounting/receipts/', [('accounting', 'receiptvoucher')]),
            ('/accounting/payments/', [('accounting', 'paymentvoucher')]),
            ('/accounting/customer-statement/', [('accounting', 'account')]),
            ('/accounting/ledger/', [('accounting', 'account')]),
            ('/accounting/trial-balance/', [('accounting', 'account')]),
            ('/accounting/profit-loss/', [('accounting', 'account')]),
            ('/accounting/', [('accounting', 'account')]),
        ]

        for prefix, models_list in permission_map:
            if path.startswith(prefix):
                report_like_paths = [
                    '/reports/sales/',
                    '/reports/commissions/',
                    '/maintenance/reports/',
                    '/accounting/customer-statement/',
                    '/accounting/ledger/',
                    '/accounting/trial-balance/',
                    '/accounting/profit-loss/',
                ]
                current_action = 'view' if any(path.startswith(x) for x in report_like_paths) else action
                return self.build_permissions(current_action, models_list)

        return []