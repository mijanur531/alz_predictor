from datetime import timedelta

import pytest
from django.utils import timezone
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

    def test_public_can_browse_and_select_doctor_booking_page(self, client, doctor_specialist):
        response = client.get(
            reverse("appointment_booking"),
            {"doctor": doctor_specialist.pk, "department": doctor_specialist.department},
        )
        assert response.status_code == 200
        assert b"Sign in to book" in response.content
        assert response.context["selected_doctor"] == doctor_specialist

    def test_non_patient_cannot_submit_booking(self, client, doctor_user, doctor_specialist):
        client.force_login(doctor_user)
        response = client.post(reverse("appointment_booking"), {
            "doctor": doctor_specialist.pk,
            "appointment_date": (timezone.localdate() + timedelta(days=1)).isoformat(),
            "time_slot": "10:30 AM - 11:30 AM",
        })
        assert response.status_code == 302
        assert response.url == reverse("home")

    def test_patient_books_appointment_post(self, client, patient_user, doctor_specialist):
        client.force_login(patient_user)
        url = reverse('appointment_booking')
        appointment_date = timezone.localdate() + timedelta(days=1)
        
        post_data = {
            "doctor": doctor_specialist.id,
            "appointment_date": appointment_date.isoformat(),
            "time_slot": "10:30 AM - 11:30 AM",
            "reason": "Routine memory check"
        }
        
        res = client.post(url, post_data)
        assert res.status_code == 302  # Redirects on success
        assert res.url == f"{url}?doctor={doctor_specialist.id}"
        
        # Verify Appointment created
        appointment = Appointment.objects.filter(patient=patient_user.patient_profile, doctor=doctor_specialist).first()
        assert appointment is not None
        assert appointment.appointment_date == appointment_date
        assert appointment.time_slot == "10:30 AM - 11:30 AM"
        assert appointment.status == "Confirmed"
        
        # Verify Audit Log created by signal
        assert AuditLog.objects.filter(user=patient_user, action="appointment_booked").exists()
        
        # Verify email dispatched via signal
        assert len(mail.outbox) >= 1
        sent_email = mail.outbox[-1]
        assert "Appointment Confirmed" in sent_email.subject
        assert "Dr. Aris Thorne" in sent_email.subject

    def test_duplicate_slot_is_rejected(self, client, patient_user, doctor_specialist):
        client.force_login(patient_user)
        appointment_date = timezone.localdate() + timedelta(days=2)
        payload = {
            "doctor": doctor_specialist.pk,
            "appointment_date": appointment_date.isoformat(),
            "time_slot": "09:00 AM - 10:00 AM",
        }
        first_response = client.post(reverse("appointment_booking"), payload)
        second_response = client.post(reverse("appointment_booking"), payload)
        assert first_response.status_code == 302
        assert second_response.status_code == 200
        assert second_response.context["booking_form"].errors["time_slot"]
        assert Appointment.objects.filter(
            doctor=doctor_specialist,
            appointment_date=appointment_date,
            time_slot=payload["time_slot"],
        ).count() == 1

    def test_homepage_specialists_use_live_directory(self, client, doctor_specialist):
        response = client.get(reverse("home"))
        assert response.status_code == 200
        assert doctor_specialist.name in response.content.decode()
        assert f"?doctor={doctor_specialist.pk}" in response.content.decode()
