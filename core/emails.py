from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)

def send_welcome_email(user):
    """
    Sends a welcome email to newly registered users.
    """
    try:
        subject = "Welcome to AlzPredictor Healthcare Platform"
        context = {
            "user": user,
            "login_url": "http://127.0.0.1:8000/login/",
            "role": user.get_role_display()
        }
        
        message = (
            f"Hello {user.first_name or user.username},\n\n"
            f"Welcome to the AlzPredictor & Health Diagnostics Platform!\n"
            f"Your account has been created with the role: {user.get_role_display()}.\n\n"
            f"You can log in and access your portal here: http://127.0.0.1:8000/login/\n\n"
            f"Best regards,\nAlzPredictor Medical Team"
        )
        
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@alzpredictor.com')
        recipient_list = [user.email] if user.email else []
        
        if recipient_list:
            send_mail(subject, message, from_email, recipient_list, fail_silently=True)
            logger.info(f"Welcome email dispatched to {user.email}")
            return True
    except Exception as e:
        logger.error(f"Failed to send welcome email: {e}")
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
            f"View Full Report: http://127.0.0.1:8000/dashboard/\n\n"
            f"Best regards,\nAlzPredictor Clinical Department"
        )
        
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@alzpredictor.com')
        recipient_list = [user.email] if user.email else []
        
        if recipient_list:
            send_mail(subject, message, from_email, recipient_list, fail_silently=True)
            logger.info(f"Prediction report email sent to {user.email}")
            return True
    except Exception as e:
        logger.error(f"Failed to send prediction report email: {e}")
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
            f"Reason: {appointment.reason or 'General Consultation'}\n"
            f"Status: {appointment.status}\n"
            f"----------------------------------------\n\n"
            f"Location: AlzPredictor Hospital Medical Center / Online Consultation\n\n"
            f"Manage Appointments: http://127.0.0.1:8000/dashboard/\n\n"
            f"Best regards,\nAlzPredictor Appointments Desk"
        )
        
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'appointments@alzpredictor.com')
        recipients = [patient_user.email] if patient_user.email else []
        if doctor.email:
            recipients.append(doctor.email)
            
        if recipients:
            send_mail(subject, message, from_email, recipients, fail_silently=True)
            logger.info(f"Appointment confirmation email sent for #{appointment.id}")
            return True
    except Exception as e:
        logger.error(f"Failed to send appointment confirmation email: {e}")
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
            f"http://127.0.0.1:8000/service/dashboard/\n\n"
            f"AlzPredictor Emergency Triage System"
        )
        
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'alerts@alzpredictor.com')
        staff_recipients = getattr(settings, 'STAFF_ALERT_EMAILS', ['staff@alzpredictor.com', 'doctor@alzpredictor.com'])
        
        send_mail(subject, message, from_email, staff_recipients, fail_silently=True)
        logger.info(f"Critical alert email dispatched for contact #{contact_message.id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send critical alert email: {e}")
    return False
