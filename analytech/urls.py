from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from app_inventory.views import dashboard

urlpatterns = [
    path('admin/', admin.site.urls),

    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('', dashboard, name='dashboard'),

    path('customers/', include('customers.urls')),
    path('devices/', include('app_devices.urls')),
    path('employees/', include('app_employees.urls')),

    path('quotations/', include('app_quotations.urls')),
    path('sales-orders/', include('app_sales.urls')),
    path('invoices/', include('app_invoices.urls')),
    path('reports/', include('app_reports.urls')),

    path('maintenance/', include('app_maintenance.urls')),
    path('inventory/', include('app_inventory.urls')),
    path('accounting/', include('accounting.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)