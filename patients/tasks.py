from celery import shared_task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from accounts.models import PatientProfile, User
from management.models import AuditLog
from core.model_loader import predict_alzheimer
import logging

logger = logging.getLogger(__name__)

@shared_task(name='patients.tasks.run_prediction_task')
def run_prediction_task(patient_profile_id, features):
    """
    Runs the Alzheimer's risk assessment asynchronously,
    saves the result to the DB, updates audit logs,
    and sends WS notifications to the patient and dashboard.
    """
    from patients.models import PredictionRecord
    
    try:
        profile = PatientProfile.objects.get(id=patient_profile_id)
        
        # Run prediction
        result = predict_alzheimer(features)
        
        # Create record
        record = PredictionRecord.objects.create(
            patient=profile,
            input_features=features,
            prediction_class=result["class"],
            probability=result["probability"],
            model_version=result["version"]
        )
        
        # Log to audit trail
        AuditLog.objects.create(
            user=profile.user,
            action="prediction_completed",
            metadata={
                "prediction_id": record.id,
                "class": record.prediction_class,
                "probability": record.probability,
                "model_version": record.model_version
            }
        )
        
        # Push notification to the Patient Group
        channel_layer = get_channel_layer()
        if channel_layer:
            payload = {
                "id": record.id,
                "class": record.prediction_class,
                "probability": record.probability,
                "model_version": record.model_version,
                "created_at": record.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                "status": "SUCCESS"
            }
            async_to_sync(channel_layer.group_send)(
                f"patient_{profile.user.id}",
                {
                    "type": "prediction_result",
                    "data": payload
                }
            )
            
            # Broadcast update to the management dashboard group
            async_to_sync(channel_layer.group_send)(
                "management_dashboard",
                {
                    "type": "dashboard_update",
                    "data": {
                        "event": "new_prediction",
                        "data": {
                            "id": record.id,
                            "patient_name": profile.user.get_full_name() or profile.user.username,
                            "class": record.prediction_class,
                            "probability": record.probability,
                            "timestamp": record.created_at.strftime('%H:%M:%S')
                        }
                    }
                }
            )
        
        return {
            "record_id": record.id,
            "class": record.prediction_class,
            "probability": record.probability
        }
        
    except Exception as e:
        logger.exception("Failed to run prediction task")
        # Send error details via WS
        channel_layer = get_channel_layer()
        if channel_layer:
            try:
                # Find patient user ID from profile id if possible
                profile = PatientProfile.objects.get(id=patient_profile_id)
                async_to_sync(channel_layer.group_send)(
                    f"patient_{profile.user.id}",
                    {
                        "type": "prediction_result",
                        "data": {
                            "status": "ERROR",
                            "message": str(e)
                        }
                    }
                )
            except Exception:
                pass
        raise e


@shared_task(name='patients.tasks.process_contact_message')
def process_contact_message(message_id):
    """
    Processes the submitted contact message.
    If is_critical is True, broadcasts a critical real-time alert to staff.
    """
    from patients.models import ContactMessage
    
    try:
        message = ContactMessage.objects.get(id=message_id)
        channel_layer = get_channel_layer()
        
        if channel_layer:
            # If critical, send alert to staff_alerts websocket group
            if message.is_critical:
                async_to_sync(channel_layer.group_send)(
                    "staff_alerts",
                    {
                        "type": "critical_alert",
                        "data": {
                            "id": message.id,
                            "name": message.name,
                            "email": message.email,
                            "message": message.message,
                            "timestamp": message.created_at.strftime('%Y-%m-%d %H:%M:%S')
                        }
                    }
                )
                
                # Also notify management dashboard of a critical event
                async_to_sync(channel_layer.group_send)(
                    "management_dashboard",
                    {
                        "type": "dashboard_update",
                        "data": {
                            "event": "critical_contact",
                            "data": {
                                "id": message.id,
                                "name": message.name,
                                "email": message.email,
                                "timestamp": message.created_at.strftime('%H:%M:%S')
                            }
                        }
                    }
                )
                
        return {"status": "processed", "is_critical": message.is_critical}
        
    except Exception as e:
        logger.exception("Failed to process contact message")
        raise e
