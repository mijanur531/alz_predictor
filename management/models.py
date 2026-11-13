from django.db import models
from accounts.models import User

class AuditLog(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_logs")
    action = models.CharField(max_length=100)
    metadata = models.JSONField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=("-timestamp",), name="audit_timestamp_idx"),
            models.Index(fields=("user", "-timestamp"), name="audit_user_timestamp_idx"),
            models.Index(fields=("action", "-timestamp"), name="audit_action_timestamp_idx"),
        ]

    def __str__(self):
        actor = self.user.username if self.user else "System"
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {actor} - {self.action}"


class ApiTestRun(models.Model):
    CHECK_CHOICES = [
        ("api_root", "API root"),
        ("health", "Health check"),
        ("schema", "OpenAPI schema"),
    ]
    STATUS_CHOICES = [
        ("passed", "Passed"),
        ("failed", "Failed"),
    ]

    operation = models.CharField(max_length=30, choices=CHECK_CHOICES)
    endpoint = models.CharField(max_length=100)
    method = models.CharField(max_length=10, default="GET")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    response_status = models.PositiveSmallIntegerField(null=True, blank=True)
    duration_ms = models.PositiveIntegerField()
    details = models.JSONField(default=dict)
    executed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="api_test_runs",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("-created_at",), name="api_test_run_created_idx"),
            models.Index(fields=("operation", "-created_at"), name="api_test_run_operation_idx"),
        ]

    def __str__(self):
        return f"{self.check} - {self.status} ({self.created_at:%Y-%m-%d %H:%M:%S})"
