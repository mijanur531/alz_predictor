from channels.generic.websocket import AsyncJsonWebsocketConsumer
import logging

logger = logging.getLogger(__name__)

class DashboardConsumer(AsyncJsonWebsocketConsumer):
    """
    Consumer for the management dashboard. Broadcasts user counts, 
    live prediction metrics, and system audit logs.
    """
    async def connect(self):
        user = self.scope.get("user")
        if user and user.is_authenticated and user.role == "management":
            await self.channel_layer.group_add("management_dashboard", self.channel_name)
            await self.accept()
            logger.info(f"Dashboard WS connected: {user.username}")
        else:
            logger.warning("Rejected unauthenticated or non-management dashboard WS request")
            await self.close()

    async def disconnect(self, close_code):
        user = self.scope.get("user")
        if user and user.is_authenticated and user.role == "management":
            await self.channel_layer.group_discard("management_dashboard", self.channel_name)

    async def dashboard_update(self, event):
        """
        Triggered when a Celery task or DB action publishes an update.
        """
        await self.send_json(event["data"])


class PatientConsumer(AsyncJsonWebsocketConsumer):
    """
    Consumer for patient individual WS channel to update prediction progress.
    """
    async def connect(self):
        user = self.scope.get("user")
        if user and user.is_authenticated and user.role == "patient":
            self.group_name = f"patient_{user.id}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
            logger.info(f"Patient WS connected: {user.username}")
        else:
            logger.warning("Rejected unauthenticated or non-patient WS request")
            await self.close()

    async def disconnect(self, close_code):
        user = self.scope.get("user")
        if user and user.is_authenticated and user.role == "patient":
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def prediction_result(self, event):
        """
        Triggered when prediction Celery task completes.
        """
        await self.send_json(event["data"])


class StaffAlertConsumer(AsyncJsonWebsocketConsumer):
    """
    Consumer for staff alerts. Broadcasts real-time priority alerts to active staff (doctors/nurses).
    """
    async def connect(self):
        user = self.scope.get("user")
        if user and user.is_authenticated and user.role in ("doctor", "nurse", "management"):
            await self.channel_layer.group_add("staff_alerts", self.channel_name)
            await self.accept()
            logger.info(f"Staff Alerts WS connected: {user.username}")
        else:
            logger.warning("Rejected unauthenticated or non-staff alerts WS request")
            await self.close()

    async def disconnect(self, close_code):
        user = self.scope.get("user")
        if user and user.is_authenticated and user.role in ("doctor", "nurse", "management"):
            await self.channel_layer.group_discard("staff_alerts", self.channel_name)

    async def critical_alert(self, event):
        """
        Triggered when a critical contact message is processed.
        """
        await self.send_json({
            "type": "CRITICAL_ALERT",
            "message": event["data"]
        })
