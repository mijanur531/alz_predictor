from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .models import Doctor, Appointment

class AppointmentBookingView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.role != 'patient':
            messages.warning(request, "Only registered patients can access medical appointment scheduling.")
            return redirect('home')
        
        doctors = Doctor.objects.filter(is_active=True).order_by('department', 'name')
        patient_appointments = Appointment.objects.filter(patient=request.user.patient_profile).order_by('-appointment_date', '-created_at')
        
        context = {
            'doctors': doctors,
            'appointments': patient_appointments,
            'departments': Doctor.DEPARTMENT_CHOICES,
        }
        return render(request, 'appointments/booking.html', context)

    def post(self, request):
        if request.user.role != 'patient':
            return redirect('home')
            
        doctor_id = request.POST.get('doctor_id')
        appointment_date = request.POST.get('appointment_date')
        time_slot = request.POST.get('time_slot')
        reason = request.POST.get('reason', '')
        
        if not doctor_id or not appointment_date or not time_slot:
            messages.error(request, "Please provide all required appointment fields.")
            return redirect('appointment_booking')
            
        doctor = get_object_or_404(Doctor, id=doctor_id, is_active=True)
        appointment = Appointment.objects.create(
            patient=request.user.patient_profile,
            doctor=doctor,
            appointment_date=appointment_date,
            time_slot=time_slot,
            reason=reason,
            status="Confirmed"
        )
        messages.success(request, f"Appointment booked successfully with {doctor.name} for {appointment_date} at {time_slot}!")
        return redirect('appointment_booking')

