from django.urls import path
from .views import customer_list, customer_create, customer_edit, customer_detail

urlpatterns = [
    path('', customer_list, name='customer_list'),
    path('new/', customer_create, name='customer_create'),
    path('<int:customer_id>/', customer_detail, name='customer_detail'),
    path('<int:customer_id>/edit/', customer_edit, name='customer_edit'),
]