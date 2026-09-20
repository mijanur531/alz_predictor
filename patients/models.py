from django.db import models
from accounts.models import User, PatientProfile

class PredictionRecord(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="predictions")
    input_features = models.JSONField()
    prediction_class = models.CharField(max_length=30)  # e.g., Normal, MCI, Dementia
    probability = models.FloatField()  # Confidence score (0.0 to 1.0 or percentage)
    model_version = models.CharField(max_length=20)
    reviewed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="reviewed_predictions")
    review_comments = models.TextField(blank=True, null=True)
    is_reviewed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Prediction for {self.patient.user.username} - {self.prediction_class} ({self.created_at.strftime('%Y-%m-%d')})"

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    is_critical = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name} (Critical: {self.is_critical})"


class VRTestRecord(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="vr_records")
    time_taken = models.FloatField(help_text="Time taken in seconds")
    errors = models.IntegerField(help_text="Navigation errors or incorrect recalls")
    score = models.FloatField(help_text="Overall score out of 100")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"VR Test for {self.patient.user.username} - Score: {self.score} ({self.created_at.strftime('%Y-%m-%d')})"

