from django.db import models

class TrainedModelArtifact(models.Model):
    name = models.CharField(max_length=100)
    model_type = models.CharField(max_length=50)  # e.g., 'Random Forest', 'Deep Learning MLP'
    hyperparameters = models.JSONField(help_text="Selected hyperparameters")
    metrics = models.JSONField(help_text="Accuracy, loss, validation metrics")
    is_active = models.BooleanField(default=False, help_text="Set as current active prediction model")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.model_type}) - Active: {self.is_active}"
