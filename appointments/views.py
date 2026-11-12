from django.contrib.auth.views import redirect_to_login
from django.db import IntegrityError, transaction
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django.utils.http import urlencode
from django.contrib import messages
from .models import Doctor, Appointment
from .forms import AppointmentBookingForm

class AppointmentBookingView(View):
    template_name = "appointments/booking.html"

    def get_context_data(self, request, form=None):
        doctors = Doctor.objects.filter(is_active=True).order_by("department", "name")
        department = request.GET.get("department", "")
        if department in dict(Doctor.DEPARTMENT_CHOICES):
            doctors = doctors.filter(department=department)

        selected_doctor = None
        doctor_id = request.GET.get("doctor")
        if doctor_id and doctor_id.isdecimal():
            selected_doctor = Doctor.objects.filter(pk=doctor_id, is_active=True).first()
            if selected_doctor:
                form = form or AppointmentBookingForm(initial={"doctor": selected_doctor.pk})
        form = form or AppointmentBookingForm()

        patient_appointments = Appointment.objects.none()
        if request.user.is_authenticated and request.user.role == "patient":
            patient_appointments = Appointment.objects.filter(
                patient=request.user.patient_profile
            ).select_related("doctor").order_by("-appointment_date", "-created_at")

        return {
            "doctors": doctors,
            "appointments": patient_appointments,
            "departments": Doctor.DEPARTMENT_CHOICES,
            "booking_form": form,
            "selected_doctor": selected_doctor,
            "selected_department": department,
        }

    def get(self, request):
        return render(request, self.template_name, self.get_context_data(request))

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect_to_login(
                request.get_full_path(),
                login_url=reverse("login"),
            )
        if request.user.role != "patient":
            messages.warning(request, "Only patient accounts can book appointments.")
            return redirect("home")

        form = AppointmentBookingForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = request.user.patient_profile
            appointment.status = "Confirmed"
            try:
                with transaction.atomic():
                    appointment.save()
            except IntegrityError:
                form.add_error(
                    "time_slot",
                    "That specialist's selected time is no longer available. Choose another slot.",
                )
            else:
                messages.success(
                    request,
                    f"Your appointment with {appointment.doctor.name} is confirmed.",
                )
                query = urlencode({"doctor": appointment.doctor_id})
                return redirect(f"{reverse('appointment_booking')}?{query}")

        return render(
            request,
            self.template_name,
            self.get_context_data(request, form=form),
        )

