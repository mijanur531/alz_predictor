import re

import pytest
from django.test import override_settings
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
        assert res.url == reverse("patient_dashboard")
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
            'role': 'management',
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
        assert res.url == reverse("login")
        assert not client.session.get("_auth_user_id")
        
        assert 'user_role' not in res.cookies
        assert 'username' not in res.cookies
        registered_user = User.objects.get(username="new_patient_reg")
        assert registered_user.role == "patient"
        
        # Check welcome email sent via signal
        assert len(mail.outbox) >= 1
        assert "Welcome to AlzPredictor" in mail.outbox[0].subject

    @pytest.mark.parametrize(
        ("role", "destination"),
        [
            ("patient", "patient_dashboard"),
            ("doctor", "service_dashboard"),
            ("nurse", "service_dashboard"),
            ("management", "management_dashboard"),
        ],
    )
    def test_login_redirects_each_role_to_its_dashboard(self, client, db, role, destination):
        user = User.objects.create_user(
            username=f"login_{role}",
            password="SecurePassword456!",
            role=role,
        )
        response = client.post(reverse("login"), {
            "username": user.username,
            "password": "SecurePassword456!",
        })
        assert response.status_code == 302
        assert response.url == reverse(destination)

    def test_login_honors_local_next_url(self, client, patient_user):
        response = client.post(
            f"{reverse('login')}?next={reverse('appointment_booking')}",
            {"username": patient_user.username, "password": "password123"},
        )
        assert response.status_code == 302
        assert response.url == reverse("appointment_booking")


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_password_reset_flow(client):
    from django.core import mail

    user = User.objects.create_user(
        username="reset_patient",
        email="reset@example.com",
        password="InitialPassword123!",
        role="patient",
    )
    mail.outbox.clear()

    response = client.post(reverse("password_reset"), {"email": user.email})
    assert response.status_code == 302
    assert response.url == reverse("password_reset_done")
    assert len(mail.outbox) == 1

    reset_link = re.search(r"http://testserver(/reset/\S+)", mail.outbox[0].body)
    assert reset_link is not None
    reset_path = reset_link.group(1)

    response = client.get(reset_path)
    assert response.status_code == 302
    confirm_path = response.url
    assert client.get(confirm_path).status_code == 200

    mismatch_response = client.post(confirm_path, {
        "new_password1": "NewSecurePassword456!",
        "new_password2": "DifferentPassword789!",
    })
    assert mismatch_response.status_code == 200
    assert "new_password2" in mismatch_response.context["form"].errors
    user.refresh_from_db()
    assert user.check_password("InitialPassword123!")

    response = client.post(confirm_path, {
        "new_password1": "NewSecurePassword456!",
        "new_password2": "NewSecurePassword456!",
    })
    assert response.status_code == 302
    assert response.url == reverse("password_reset_complete")

    user.refresh_from_db()
    assert user.check_password("NewSecurePassword456!")
    complete_response = client.get(reverse("password_reset_complete"))
    assert b"content=\"5;url=/login/\"" in complete_response.content


@pytest.mark.django_db
def test_api_token_page_requires_login_and_generates_tokens(client):
    user = User.objects.create_user(
        username="token_page_user",
        password="InitialPassword123!",
        role="patient",
    )

    response = client.get(reverse("api_token_page"))
    assert response.status_code == 302
    assert reverse("login") in response.url

    client.force_login(user)
    response = client.post(reverse("api_token_page"))
    assert response.status_code == 200
    assert b"access-token" in response.content
    assert b"refresh-token" in response.content

