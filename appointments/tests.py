import pytest
from django.urls import reverse
from django.core import mail
from accounts.models import User
from appointments.models import Doctor, Appointment
from management.models import AuditLog

@pytest.fixture
def doctor_specialist(db):
    return Doctor.objects.create(
        name="Dr. Aris Thorne",
        specialty="Neuro-Geriatric Cognitive Specialist",
        department="Neurology",
        qualification="MD, PhD",
        experience_years=16,
        rating=4.98,
        consultation_fee=180,
        email="aris.thorne@alzpredictor.com",
        phone="+1 555-0199"
    )

@pytest.fixture
def patient_user(db):
    user = User.objects.create_user(username="test_patient_appt", password="password123", email="patient@test.com", role="patient")
    return user

@pytest.fixture
def doctor_user(db):
    user = User.objects.create_user(username="test_doctor_appt", password="password123", email="doctor@test.com", role="doctor")
    return user

@pytest.mark.django_db
class TestAppointmentSystem:
    def test_doctor_creation(self, doctor_specialist):
        assert doctor_specialist.name == "Dr. Aris Thorne"
        assert doctor_specialist.department == "Neurology"
        assert doctor_specialist.consultation_fee == 180
        assert doctor_specialist.is_active is True

    def test_patient_can_view_booking_page(self, client, patient_user, doctor_specialist):
        client.force_login(patient_user)
        url = reverse('appointment_booking')
        res = client.get(url)
        assert res.status_code == 200
        assert doctor_specialist.name in res.content.decode()

    def test_non_patient_redirected_from_booking(self, client, doctor_user):
        client.force_login(doctor_user)
        url = reverse('appointment_booking')
        res = client.get(url)
        assert res.status_code == 302

    def test_patient_books_appointment_post(self, client, patient_user, doctor_specialist):
        client.force_login(patient_user)
        url = reverse('appointment_booking')
        
        post_data = {
            "doctor_id": doctor_specialist.id,
            "appointment_date": "2026-10-15",
            "time_slot": "10:00 AM - 10:45 AM",
            "reason": "Routine memory check"
        }
        
        res = client.post(url, post_data)
        assert res.status_code == 302  # Redirects on success
        
        # Verify Appointment created
        appointment = Appointment.objects.filter(patient=patient_user.patient_profile, doctor=doctor_specialist).first()
        assert appointment is not None
        assert str(appointment.appointment_date) == "2026-10-15"
        assert appointment.time_slot == "10:00 AM - 10:45 AM"
        assert appointment.status == "Confirmed"
        
        # Verify Audit Log created by signal
        assert AuditLog.objects.filter(user=patient_user, action="appointment_booked").exists()
        
        # Verify email dispatched via signal
        assert len(mail.outbox) >= 1
        sent_email = mail.outbox[-1]
        assert "Appointment Confirmed" in sent_email.subject
        assert "Dr. Aris Thorne" in sent_email.subject
