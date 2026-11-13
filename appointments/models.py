from django.db import models
from django.db.models import Q
from accounts.models import PatientProfile

class Doctor(models.Model):
    DEPARTMENT_CHOICES = [
        ("Neurology", "Neurology"),
        ("Cardiology", "Cardiology"),
        ("Geriatrics", "Geriatrics"),
        ("Gastroenterology", "Gastroenterology"),
        ("Orthopedics", "Orthopedics"),
        ("Radiology", "Radiology"),
        ("General Medicine", "General Medicine"),
    ]

    name = models.CharField(max_length=150)
    specialty = models.CharField(max_length=100)
    department = models.CharField(max_length=100, choices=DEPARTMENT_CHOICES, default="Neurology")
    qualification = models.CharField(max_length=150)
    experience_years = models.PositiveIntegerField(default=10)
    rating = models.FloatField(default=4.9)
    consultation_fee = models.PositiveIntegerField(default=150)
    avatar_url = models.CharField(max_length=255, default="https://images.unsplash.com/photo-1622253692010-333f2da6031d?w=300&h=300&fit=crop&crop=face")
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, default="+1 (800) 456-7890")
    bio = models.TextField(blank=True)
    available_days = models.CharField(max_length=100, default="Mon, Tue, Wed, Thu, Fri")
    available_hours = models.CharField(max_length=50, default="09:00 AM - 05:00 PM")
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=("is_active", "department", "name"), name="doctor_directory_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(experience_years__gte=0),
                name="doctor_experience_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(rating__gte=0) & Q(rating__lte=5),
                name="doctor_rating_0_5",
            ),
            models.CheckConstraint(
                condition=Q(consultation_fee__gte=0),
                name="doctor_fee_nonnegative",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.specialty})"


class Appointment(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Confirmed", "Confirmed"),
        ("Completed", "Completed"),
        ("Cancelled", "Cancelled"),
    ]

    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="appointments")
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="appointments")
    appointment_date = models.DateField()
    time_slot = models.CharField(max_length=50)
    reason = models.TextField(blank=True, help_text="Reason for consultation / symptoms")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="Confirmed")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=("patient", "-appointment_date"), name="appointment_patient_date_idx"),
            models.Index(fields=("doctor", "appointment_date"), name="appointment_doctor_date_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=("doctor", "appointment_date", "time_slot"),
                condition=~Q(status="Cancelled"),
                name="unique_active_doctor_slot",
            ),
        ]

    def __str__(self):
        return f"Appointment with {self.doctor.name} for {self.patient.user.username} on {self.appointment_date} ({self.time_slot})"
