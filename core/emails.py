from django.core.mail import send_mail, send_mass_mail
from django.conf import settings
from django.urls import reverse
from smtplib import SMTPException
import logging

logger = logging.getLogger(__name__)


def _absolute_url(path):
    return f"{settings.SITE_URL.rstrip('/')}{path}"


def send_bulk_email(subject, message, recipients, from_email=None):
    """Deliver one private message per recipient using the configured backend."""
    unique_recipients = list(dict.fromkeys(email.strip() for email in recipients if email and email.strip()))
    if not unique_recipients:
        return 0

    sender = from_email or settings.DEFAULT_FROM_EMAIL
    batch_size = max(1, getattr(settings, "BULK_EMAIL_BATCH_SIZE", 50))
    sent_count = 0
    for start in range(0, len(unique_recipients), batch_size):
        batch = unique_recipients[start:start + batch_size]
        messages = [(subject, message, sender, [recipient]) for recipient in batch]
        sent_count += send_mass_mail(messages, fail_silently=False)
    return sent_count


def send_welcome_email(user):
    """
    Sends a welcome email to newly registered users.
    """
    try:
        subject = "Welcome to AlzPredictor Healthcare Platform"
        login_url = _absolute_url(reverse('login'))
        message = (
            f"Hello {user.first_name or user.username},\n\n"
            f"Welcome to the AlzPredictor & Health Diagnostics Platform!\n"
            f"Your account has been created with the role: {user.get_role_display()}.\n\n"
            f"You can sign in here: {login_url}\n\n"
            f"Best regards,\nAlzPredictor Medical Team"
        )
        
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@alzpredictor.com')
        recipient_list = [user.email] if user.email else []
        
        if recipient_list:
            send_bulk_email(subject, message, recipient_list, from_email)
            logger.info("Welcome email dispatched for user %s", user.pk)
            return True
    except (OSError, SMTPException):
        logger.exception("Failed to send welcome email for user %s", user.pk)
    return False


def send_prediction_report_email(user, prediction_record):
    """
    Sends a diagnostic summary email when an Alzheimer's prediction is completed.
    """
    try:
        subject = f"Diagnostic Assessment Summary - {prediction_record.prediction_class}"
        message = (
            f"Dear {user.get_full_name() or user.username},\n\n"
            f"Your AI Alzheimer's risk assessment has been completed.\n\n"
            f"Summary of Results:\n"
            f"----------------------------------------\n"
            f"Assessed Risk Class: {prediction_record.prediction_class}\n"
            f"Confidence Probability: {round(prediction_record.probability * 100, 1)}%\n"
            f"Model Version: {prediction_record.model_version}\n"
            f"Date of Assessment: {prediction_record.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"----------------------------------------\n\n"
            f"Clinical Notice: This assessment is an academic prototype and is not a certified diagnostic tool.\n"
            f"We encourage you to book a consultation with our neurology specialists on the portal.\n\n"
            f"View Full Report: {_absolute_url(reverse('patient_dashboard'))}\n\n"
            f"Best regards,\nAlzPredictor Clinical Department"
        )
        
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@alzpredictor.com')
        recipient_list = [user.email] if user.email else []
        
        if recipient_list:
            send_bulk_email(subject, message, recipient_list, from_email)
            logger.info("Prediction report email sent for user %s", user.pk)
            return True
    except (OSError, SMTPException):
        logger.exception("Failed to send prediction report email for user %s", user.pk)
    return False


def send_appointment_confirmation_email(appointment):
    """
    Sends booking confirmation email to patient and doctor.
    """
    try:
        patient_user = appointment.patient.user
        doctor = appointment.doctor
        
        subject = f"Appointment Confirmed with {doctor.name} on {appointment.appointment_date}"
        message = (
            f"Dear {patient_user.get_full_name() or patient_user.username},\n\n"
            f"Your medical consultation has been successfully booked!\n\n"
            f"Appointment Details:\n"
            f"----------------------------------------\n"
            f"Doctor: {doctor.name} ({doctor.specialty})\n"
            f"Department: {doctor.department}\n"
            f"Date: {appointment.appointment_date}\n"
            f"Time Slot: {appointment.time_slot}\n"
            f"Status: {appointment.status}\n"
            f"----------------------------------------\n\n"
            f"Location: AlzPredictor Hospital Medical Center / Online Consultation\n\n"
            f"Manage Appointments: {_absolute_url(reverse('appointment_booking'))}\n\n"
            f"Best regards,\nAlzPredictor Appointments Desk"
        )
        
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'appointments@alzpredictor.com')
        recipients = [patient_user.email] if patient_user.email else []
        if doctor.email:
            recipients.append(doctor.email)
            
        if recipients:
            send_mail(subject, message, from_email, recipients)
            logger.info("Appointment confirmation email sent for #%s", appointment.id)
            return True
    except (OSError, SMTPException):
        logger.exception("Failed to send appointment confirmation email for appointment %s", appointment.pk)
    return False


def send_critical_alert_email(contact_message):
    """
    Sends high-priority alert email to on-duty staff when a critical contact is submitted.
    """
    try:
        subject = f"URGENT: Critical Clinical Alert from {contact_message.name}"
        message = (
            f"CRITICAL MEDICAL ALERT NOTIFICATION\n"
            f"========================================\n"
            f"Sender Name: {contact_message.name}\n"
            f"Sender Email: {contact_message.email}\n"
            f"Submitted At: {contact_message.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Message Content:\n"
            f"\"{contact_message.message}\"\n"
            f"========================================\n\n"
            f"Action Required: Please review this inquiry immediately on the Clinical Intake Board:\n"
            f"{_absolute_url(reverse('service_dashboard'))}\n\n"
            f"AlzPredictor Emergency Triage System"
        )
        
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'alerts@alzpredictor.com')
        staff_recipients = getattr(settings, 'STAFF_ALERT_EMAILS', ['staff@alzpredictor.com', 'doctor@alzpredictor.com'])
        
        send_mail(subject, message, from_email, staff_recipients)
        logger.info("Critical alert email dispatched for contact #%s", contact_message.id)
        return True
    except (OSError, SMTPException):
        logger.exception("Failed to send critical alert email for contact %s", contact_message.id)
    return False
