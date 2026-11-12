from django import forms
from django.utils import timezone

from .models import Appointment, Doctor


APPOINTMENT_TIME_SLOTS = (
    ("09:00 AM - 10:00 AM", "09:00 AM - 10:00 AM"),
    ("10:30 AM - 11:30 AM", "10:30 AM - 11:30 AM"),
    ("01:00 PM - 02:00 PM", "01:00 PM - 02:00 PM"),
    ("02:30 PM - 03:30 PM", "02:30 PM - 03:30 PM"),
    ("04:00 PM - 05:00 PM", "04:00 PM - 05:00 PM"),
)


class AppointmentBookingForm(forms.ModelForm):
    time_slot = forms.ChoiceField(choices=APPOINTMENT_TIME_SLOTS)

    class Meta:
        model = Appointment
        fields = ("doctor", "appointment_date", "time_slot", "reason")
        widgets = {
            "doctor": forms.Select(attrs={"class": "form-select"}),
            "appointment_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"},
                format="%Y-%m-%d",
            ),
            "reason": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "maxlength": 2000,
                    "placeholder": "Optional",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["doctor"].queryset = Doctor.objects.filter(is_active=True).order_by(
            "department", "name"
        )
        self.fields["doctor"].empty_label = "Choose a specialist"
        self.fields["appointment_date"].input_formats = ["%Y-%m-%d"]
        self.fields["reason"].required = False

    def clean_appointment_date(self):
        appointment_date = self.cleaned_data["appointment_date"]
        if appointment_date < timezone.localdate():
            raise forms.ValidationError("Choose today or a future date.")
        return appointment_date

    def clean(self):
        cleaned_data = super().clean()
        doctor = cleaned_data.get("doctor")
        appointment_date = cleaned_data.get("appointment_date")
        time_slot = cleaned_data.get("time_slot")
        if doctor and appointment_date and time_slot:
            has_conflict = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=appointment_date,
                time_slot=time_slot,
            ).exclude(status="Cancelled").exists()
            if has_conflict:
                self.add_error(
                    "time_slot",
                    "That specialist's selected time is no longer available.",
                )
        return cleaned_data
