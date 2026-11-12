from django.contrib import admin  # pyright: ignore[reportMissingModuleSource]
from .models import ContactMessage, PredictionRecord, VRTestRecord


@admin.register(PredictionRecord, ContactMessage, VRTestRecord)
class PatientAdmin(admin.ModelAdmin):
    pass
