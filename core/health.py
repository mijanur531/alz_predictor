from django.conf import settings
from health_check.views import HealthCheckView


class ApplicationHealthCheckView(HealthCheckView):
    checks = tuple(
        check
        for check in HealthCheckView.checks
        if settings.HEALTH_CHECK_INCLUDE_DNS or check != "health_check.checks.DNS"
    )
