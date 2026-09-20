from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import PredictionRecord, ContactMessage
from core.emails import send_prediction_report_email, send_critical_alert_email
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=PredictionRecord)
def prediction_record_post_save_handler(sender, instance, created, **kwargs):
    if created:
        try:
            if instance.patient and instance.patient.user:
                send_prediction_report_email(instance.patient.user, instance)
                logger.info(f'Signal: Diagnostic report email triggered for prediction #{instance.id}')
        except Exception as e:
            logger.error(f'Signal error sending prediction report email #{instance.id}: {e}')

@receiver(post_save, sender=ContactMessage)
def contact_message_post_save_handler(sender, instance, created, **kwargs):
    if created and instance.is_critical:
        try:
            send_critical_alert_email(instance)
            logger.info(f'Signal: Critical alert email triggered for contact #{instance.id}')
        except Exception as e:
            logger.error(f'Signal error sending critical contact alert #{instance.id}: {e}')
