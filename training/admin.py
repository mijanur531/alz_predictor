from django.contrib import admin  # pyright: ignore[reportMissingModuleSource]
from .models import TrainedModelArtifact

@admin.register(TrainedModelArtifact)
class TrainedModelArtifactAdmin(admin.ModelAdmin):
    pass