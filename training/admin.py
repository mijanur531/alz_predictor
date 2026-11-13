from django.contrib import admin  # pyright: ignore[reportMissingModuleSource]
from .models import TrainedModelArtifact

@admin.register(TrainedModelArtifact)
class TrainedModelArtifactAdmin(admin.ModelAdmin):
    list_display = ("name", "model_type", "is_active", "created_at")
    list_filter = ("model_type", "is_active")
    search_fields = ("name", "model_type")
    readonly_fields = ("created_at",)