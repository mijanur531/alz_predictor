from django.contrib import admin # type: ignore

from .models import Appointment, Doctor


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("name", "specialty", "department", "rating", "is_active")
    list_filter = ("department", "is_active")
    search_fields = ("name", "specialty", "qualification", "email")


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("patient", "doctor", "appointment_date", "time_slot", "status")
    list_filter = ("status", "appointment_date", "doctor__department")
    search_fields = ("patient__user__username", "doctor__name", "reason")
