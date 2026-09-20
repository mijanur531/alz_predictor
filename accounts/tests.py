import pytest
from django.urls import reverse
from accounts.models import User
from patients.models import VRTestRecord

@pytest.fixture
def patient_user(db):
    user = User.objects.create_user(username="patient_vr", password="password123", role="patient")
    return user

@pytest.fixture
def doctor_user(db):
    return User.objects.create_user(username="doctor_vr", password="password123", role="doctor")

@pytest.mark.django_db
class TestVRCognitiveTask:
    def test_vr_page_restricted_to_patients(self, client, doctor_user):
        client.force_login(doctor_user)
        url = reverse('vr_test')
        res = client.get(url)
        assert res.status_code == 302 # Redirected

    def test_patient_can_access_vr(self, client, patient_user):
        client.force_login(patient_user)
        url = reverse('vr_test')
        res = client.get(url)
        assert res.status_code == 200

    def test_submit_vr_results_updates_cognitive_score(self, client, patient_user):
        client.force_login(patient_user)
        url = reverse('vr_test')
        
        # Post game metrics
        payload = {
            "time_taken": 25.5,
            "errors": 2,
            "score": 85.0
        }
        
        res = client.post(url, payload, content_type='application/json')
        assert res.status_code == 200
        assert res.json()['status'] == 'SUCCESS'
        
        # Verify 85.0 score maps to 25.5 MMSE (85% of 30)
        assert res.json()['cognitive_score'] == 25.5
        
        # Check database records
        assert VRTestRecord.objects.filter(patient=patient_user.patient_profile, score=85.0).exists()
        
        patient_user.patient_profile.refresh_from_db()
        assert patient_user.patient_profile.cognitive_score == 25.5


@pytest.mark.django_db
class TestNativeCookieSystemAndAuthSignals:
    def test_login_sets_native_cookies(self, client, db):
        user = User.objects.create_user(username="cookie_patient", password="password123", email="cookie@test.com", role="patient")
        url = reverse('login')
        
        res = client.post(url, {'username': 'cookie_patient', 'password': 'password123'})
        assert res.status_code == 302
        assert 'user_role' in res.cookies
        assert res.cookies['user_role'].value == 'patient'
        assert 'username' in res.cookies
        assert res.cookies['username'].value == 'cookie_patient'

    def test_logout_deletes_native_cookies(self, client, db):
        user = User.objects.create_user(username="logout_user", password="password123", role="patient")
        client.force_login(user)
        url = reverse('logout')
        
        res = client.post(url)
        assert res.status_code == 302
        # Verify cookie cleared/expired
        assert res.cookies['user_role'].value == '' or res.cookies['user_role']['max-age'] == 0

    def test_registration_sets_cookies_and_dispatches_welcome_email(self, client, db):
        from django.core import mail
        mail.outbox.clear()
        url = reverse('register')
        
        reg_payload = {
            'username': 'new_patient_reg',
            'email': 'new_patient@example.com',
            'password1': 'StrongPassword123!',
            'password2': 'StrongPassword123!',
            'role': 'patient',
            'first_name': 'New',
            'last_name': 'Patient',
            'age': 62,
            'gender': 'Female',
            'education_level': "Bachelor's",
            'bmi': 23.5,
            'cognitive_score': 27.5,
            'physical_activity': 3.5
        }
        
        res = client.post(url, reg_payload)
        assert res.status_code == 302
        
        # Check cookies set
        assert 'user_role' in res.cookies
        assert res.cookies['user_role'].value == 'patient'
        assert 'username' in res.cookies
        assert res.cookies['username'].value == 'new_patient_reg'
        
        # Check welcome email sent via signal
        assert len(mail.outbox) >= 1
        assert "Welcome to AlzPredictor" in mail.outbox[0].subject

