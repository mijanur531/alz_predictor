from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Appointment
from core.emails import send_appointment_confirmation_email
from management.models import AuditLog
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Appointment)
def appointment_post_save_handler(sender, instance, created, **kwargs):
    if created:
        try:
            # 1. Dispatch confirmation email
            send_appointment_confirmation_email(instance)
            
            # 2. Record in AuditLog
            AuditLog.objects.create(
                user=instance.patient.user,
                action="appointment_booked",
                metadata={
                    "appointment_id": instance.id,
                    "doctor": instance.doctor.name,
                    "department": instance.doctor.department,
                    "date": str(instance.appointment_date),
                    "time_slot": instance.time_slot
                }
            )
            logger.info(f"Signal: Appointment #{instance.id} confirmation processed.")
        except Exception as e:
            logger.error(f"Signal error handling appointment #{instance.id}: {e}")
