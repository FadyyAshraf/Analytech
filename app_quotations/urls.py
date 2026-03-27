from django.urls import path
from .views import (
    quotation_list,
    quotation_create,
    quotation_detail,
    quotation_print,
    quotation_from_visit,
)

urlpatterns = [
    path('', quotation_list, name='quotation_list'),
    path('new/', quotation_create, name='quotation_create'),
    path('<int:quotation_id>/', quotation_detail, name='quotation_detail'),
    path('print/<int:quotation_id>/', quotation_print, name='quotation_print'),
    path('from-visit/<int:visit_id>/', quotation_from_visit, name='quotation_from_visit'),
]