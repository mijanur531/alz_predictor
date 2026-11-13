from django.contrib import admin
from .models import ApiTestRun, AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "action", "user")
    list_filter = ("action", "timestamp")
    search_fields = ("action", "user__username")
    readonly_fields = ("timestamp",)


@admin.register(ApiTestRun)
class ApiTestRunAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "operation",
        "status",
        "response_status",
        "duration_ms",
        "executed_by",
    )
    list_filter = ("operation", "status", "created_at")
    search_fields = ("operation", "endpoint", "executed_by__username")
    readonly_fields = ("created_at",)
