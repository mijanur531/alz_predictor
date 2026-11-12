from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = [
        ("patient", "Patient"),
        ("doctor", "Doctor"),
        ("nurse", "Nurse"),
        ("technician", "Technician"),
        ("management", "Management"),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="patient")

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

class PatientProfile(models.Model):
    GENDER_CHOICES = [
        ("Male", "Male"),
        ("Female", "Female"),
        ("Other", "Other"),
    ]
    EDUCATION_CHOICES = [
        ("High School", "High School"),
        ("Bachelor's", "Bachelor's"),
        ("Master's", "Master's"),
        ("PhD", "PhD"),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="patient_profile")
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
    education_level = models.CharField(max_length=50, choices=EDUCATION_CHOICES, null=True, blank=True)
    bmi = models.FloatField(null=True, blank=True)
    smoking = models.BooleanField(default=False)
    cognitive_score = models.FloatField(null=True, blank=True)  # E.g. MMSE score from 0 to 30
    family_history = models.BooleanField(default=False)
    physical_activity = models.FloatField(null=True, blank=True)  # Hours/week

    def __str__(self):
        return f"Patient: {self.user.get_full_name() or self.user.username}"

class ServiceProviderProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="provider_profile")
    department = models.CharField(max_length=50)
    qualification = models.CharField(max_length=100)

    def __str__(self):
        return f"Staff: {self.user.get_full_name() or self.user.username} ({self.department})"
