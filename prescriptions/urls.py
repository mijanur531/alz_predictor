from django.urls import path
from .views import PrescriptionScannerView

urlpatterns = [
    path('prescriptions/scanner/', PrescriptionScannerView.as_view(), name='prescriptions_scanner'),
]
