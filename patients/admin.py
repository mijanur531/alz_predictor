from django.contrib import admin  # pyright: ignore[reportMissingModuleSource]
from .models import ContactMessage, PredictionRecord, VRTestRecord


@admin.register(PredictionRecord)
class PredictionRecordAdmin(admin.ModelAdmin):
    list_display = ("patient", "prediction_class", "probability", "is_reviewed", "created_at")
    list_filter = ("prediction_class", "is_reviewed", "model_version")
    search_fields = ("patient__user__username", "prediction_class", "review_comments")
    readonly_fields = ("created_at",)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "is_critical", "created_at")
    list_filter = ("is_critical", "created_at")
    search_fields = ("name", "email", "message")
    readonly_fields = ("created_at",)


@admin.register(VRTestRecord)
class VRTestRecordAdmin(admin.ModelAdmin):
    list_display = ("patient", "score", "errors", "time_taken", "created_at")
    search_fields = ("patient__user__username",)
    readonly_fields = ("created_at",)
