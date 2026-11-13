from django.db import models
from django.db.models import Q
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

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(age__isnull=True) | Q(age__lte=120),
                name="patient_age_lte_120",
            ),
            models.CheckConstraint(
                condition=Q(bmi__isnull=True) | Q(bmi__gte=10) & Q(bmi__lte=60),
                name="patient_bmi_10_60",
            ),
            models.CheckConstraint(
                condition=Q(cognitive_score__isnull=True)
                | Q(cognitive_score__gte=0) & Q(cognitive_score__lte=30),
                name="patient_cognitive_score_0_30",
            ),
            models.CheckConstraint(
                condition=Q(physical_activity__isnull=True)
                | Q(physical_activity__gte=0) & Q(physical_activity__lte=168),
                name="patient_activity_0_168",
            ),
        ]

    def __str__(self):
        return f"Patient: {self.user.get_full_name() or self.user.username}"

class ServiceProviderProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="provider_profile")
    department = models.CharField(max_length=50)
    qualification = models.CharField(max_length=100)

    class Meta:
        indexes = [
            models.Index(fields=("department",), name="provider_department_idx"),
        ]

    def __str__(self):
        return f"Staff: {self.user.get_full_name() or self.user.username} ({self.department})"
