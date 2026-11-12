from django.contrib import admin  # pyright: ignore[reportMissingModuleSource]
from .models import PrescriptionScan


@admin.register(PrescriptionScan)
class PrescriptionScanAdmin(admin.ModelAdmin):
    pass
    print("Prescription Scan Admin registered successfully.");
