from django.contrib import admin  # pyright: ignore[reportMissingModuleSource]
from .models import PrescriptionScan


@admin.register(PrescriptionScan)
class PrescriptionScanAdmin(admin.ModelAdmin):
    list_display = ("patient", "detected_medicines", "created_at")
    search_fields = ("patient__user__username", "raw_text")
    readonly_fields = ("detected_medicines", "llm_analysis", "created_at")
    print("Prescription Scan Admin registered successfully.");
