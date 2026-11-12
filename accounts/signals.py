from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, PatientProfile, ServiceProviderProfile
from core.emails import send_welcome_email

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.role == 'patient':
            PatientProfile.objects.get_or_create(user=instance)
        else:
            # Create a provider profile with placeholder values for non-patients
            ServiceProviderProfile.objects.get_or_create(
                user=instance,
                defaults={'department': 'General Medicine', 'qualification': 'MD / Nurse Practitioner / Admin'}
            )
        send_welcome_email(instance)

