from django.urls import path
from .views import AppointmentBookingView

urlpatterns = [
    path('appointments/booking/', AppointmentBookingView.as_view(), name='appointment_booking'),
    path('appointments/book/', AppointmentBookingView.as_view(), name='appointment_book_alias'),
]
