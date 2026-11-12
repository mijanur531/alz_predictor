import pytest
from django.core import mail
from django.test import override_settings

from accounts.models import User
from patients.models import ContactMessage, PredictionRecord


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_prediction_post_save_sends_report_only_on_creation():
    user = User.objects.create_user(
        username="prediction_signal_patient",
        email="prediction-signal@example.com",
        password="InitialPassword123!",
        role="patient",
    )
    mail.outbox.clear()

    record = PredictionRecord.objects.create(
        patient=user.patient_profile,
        input_features={"age": 68},
        prediction_class="MCI",
        probability=0.45,
        model_version="test",
    )
    assert len(mail.outbox) == 1
    assert "Diagnostic Assessment Summary" in mail.outbox[0].subject

    record.is_reviewed = True
    record.save()
    assert len(mail.outbox) == 1


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_contact_post_save_emails_only_critical_new_messages():
    mail.outbox.clear()
    ContactMessage.objects.create(
        name="Routine contact",
        email="routine@example.com",
        message="Routine question",
        is_critical=False,
    )
    assert len(mail.outbox) == 0

    message = ContactMessage.objects.create(
        name="Urgent contact",
        email="urgent@example.com",
        message="Please review this urgent concern",
        is_critical=True,
    )
    assert len(mail.outbox) == 1
    assert "URGENT" in mail.outbox[0].subject

    message.is_critical = False
    message.save()
    assert len(mail.outbox) == 1
