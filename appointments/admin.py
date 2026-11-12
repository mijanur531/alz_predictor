from django.contrib import admin # type: ignore

from .models import Appointment, Doctor


@admin.register(Doctor, Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    pass
