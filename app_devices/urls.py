from django.urls import path
from .views import device_list, device_create, device_edit, device_detail

urlpatterns = [
    path('', device_list, name='device_list'),
    path('new/', device_create, name='device_create'),
    path('<int:device_id>/', device_detail, name='device_detail'),
    path('<int:device_id>/edit/', device_edit, name='device_edit'),
]