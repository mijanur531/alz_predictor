from django.urls import path
from .views import AppointmentBookingView

urlpatterns = [
    path('appointments/booking/', AppointmentBookingView.as_view(), name='appointment_booking'),
]
