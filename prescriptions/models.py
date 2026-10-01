from django.db import models
from accounts.models import PatientProfile

class PrescriptionScan(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="prescription_scans")
    uploaded_image = models.ImageField(upload_to="prescriptions/", null=True, blank=True)
    raw_text = models.TextField(blank=True, help_text="Raw text extracted by OCR")
    detected_medicines = models.JSONField(default=list, blank=True, help_text="Parsed list of drug names")
    llm_analysis = models.TextField(blank=True, help_text="Clinical recommendations from LLM")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Scan for {self.patient.user.username} on {self.created_at.strftime('%Y-%m-%d')}"
