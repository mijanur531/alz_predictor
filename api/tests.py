import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from accounts.models import User, PatientProfile, ServiceProviderProfile
from patients.models import PredictionRecord, ContactMessage
from management.models import AuditLog

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def patient_user(db):
    user = User.objects.create_user(username="test_patient", password="password123", role="patient")
    # Signal auto-creates profile; retrieve it and configure baseline
    profile = user.patient_profile
    profile.age = 65
    profile.gender = "Male"
    profile.education_level = "Bachelor's"
    profile.bmi = 24.5
    profile.cognitive_score = 28.0
    profile.physical_activity = 5.0
    profile.save()
    return user

@pytest.fixture
def doctor_user(db):
    return User.objects.create_user(username="test_doctor", password="password123", role="doctor")

@pytest.fixture
def manager_user(db):
    return User.objects.create_user(username="test_manager", password="password123", role="management")


@pytest.mark.django_db
class TestUserProfiles:
    """Test user creation triggers appropriate profile signals"""
    def test_patient_profile_created(self):
        user = User.objects.create_user(username="patient_test", password="password123", role="patient")
        assert hasattr(user, 'patient_profile')
        assert not hasattr(user, 'provider_profile')
        assert isinstance(user.patient_profile, PatientProfile)

    def test_staff_profile_created(self):
        user = User.objects.create_user(username="doctor_test", password="password123", role="doctor")
        assert hasattr(user, 'provider_profile')
        assert not hasattr(user, 'patient_profile')
        assert isinstance(user.provider_profile, ServiceProviderProfile)


@pytest.mark.django_db
class TestRolePermissions:
    """Test endpoint permissions gate roles correctly"""
    def test_unauthenticated_blocked(self, api_client):
        url = reverse('api:patient_predictions')
        res = api_client.get(url)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_patient_can_access_predictions(self, api_client, patient_user):
        api_client.force_authenticate(user=patient_user)
        url = reverse('api:patient_predictions')
        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK

    def test_patient_cannot_access_management_stats(self, api_client, patient_user):
        api_client.force_authenticate(user=patient_user)
        url = reverse('api:management_stats')
        res = api_client.get(url)
        # Should be blocked
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_doctor_cannot_access_management_stats(self, api_client, doctor_user):
        api_client.force_authenticate(user=doctor_user)
        url = reverse('api:management_stats')
        res = api_client.get(url)
        # Should be blocked
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_manager_can_access_management_stats(self, api_client, manager_user):
        api_client.force_authenticate(user=manager_user)
        url = reverse('api:management_stats')
        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestPredictionWorkflow:
    """Test enqueuing predictions asynchronously"""
    def test_patient_submits_prediction(self, api_client, patient_user, mocker):
        # Mock Celery delay to avoid needing a running Redis server for unit testing
        mock_delay = mocker.patch('patients.tasks.run_prediction_task.delay')
        mock_delay.return_value.id = "mocked-task-uuid"

        api_client.force_authenticate(user=patient_user)
        url = reverse('api:predict_trigger')
        
        payload = {
            "age": 70,
            "gender": "Male",
            "education_level": "Bachelor's",
            "bmi": 26.2,
            "smoking": True,
            "cognitive_score": 24.0,
            "family_history": True,
            "physical_activity": 3.0
        }
        
        res = api_client.post(url, payload, format='json')
        assert res.status_code == status.HTTP_202_ACCEPTED
        assert res.data['task_id'] == "mocked-task-uuid"
        
        # Verify Audit Log entry was generated
        assert AuditLog.objects.filter(user=patient_user, action="prediction_requested").exists()


@pytest.mark.django_db
class TestContactSubmission:
    """Test contact submissions work publicly"""
    def test_public_contact_submission(self, api_client, mocker):
        mock_delay = mocker.patch('patients.tasks.process_contact_message.delay')
        url = reverse('api:contact_submit')
        
        payload = {
            "name": "John Doe",
            "email": "john@doe.com",
            "message": "Simple contact query details.",
            "is_critical": False
        }
        
        res = api_client.post(url, payload, format='json')
        assert res.status_code == status.HTTP_201_CREATED
        assert ContactMessage.objects.filter(email="john@doe.com").exists()
        mock_delay.assert_called_once()


@pytest.mark.django_db
class TestPrescriptionScanREST:
    def test_patient_can_scan_prescription(self, api_client, patient_user):
        api_client.force_authenticate(user=patient_user)
        # Using basename router mapping, the list route is 'api:prescriptions-list'
        url = reverse('api:prescriptions-list')
        
        payload = {
            "raw_text": "Rx: Donepezil 10mg once daily at bedtime."
        }
        
        res = api_client.post(url, payload, format='json')
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data['detected_medicines'] == ["Donepezil (Aricept)"]
        assert "Donepezil" in res.data['llm_analysis']

    def test_doctor_cannot_scan_prescription(self, api_client, doctor_user):
        api_client.force_authenticate(user=doctor_user)
        url = reverse('api:prescriptions-list')
        
        payload = {
            "raw_text": "Rx: Donepezil 10mg."
        }
        
        res = api_client.post(url, payload, format='json')
        assert res.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestModelTrainingREST:
    def test_manager_can_trigger_training(self, api_client, manager_user):
        api_client.force_authenticate(user=manager_user)
        url = reverse('api:training-list')
        
        payload = {
            "model_type": "Random Forest",
            "epochs": 3,
            "n_estimators": 50,
            "max_depth": 5
        }
        
        res = api_client.post(url, payload, format='json')
        assert res.status_code == status.HTTP_202_ACCEPTED
        assert res.data['status'] == 'STARTED'

    def test_patient_cannot_trigger_training(self, api_client, patient_user):
        api_client.force_authenticate(user=patient_user)
        url = reverse('api:training-list')
        
        payload = {
            "model_type": "Random Forest",
            "epochs": 3
        }
        
        res = api_client.post(url, payload, format='json')
        assert res.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestAppointmentsREST:
    @pytest.fixture
    def test_doctor(self, db):
        from appointments.models import Doctor
        return Doctor.objects.create(
            name="Dr. Aris Thorne",
            specialty="Neurology",
            department="Neurology",
            qualification="MD",
            consultation_fee=180
        )

    def test_list_doctors(self, api_client, test_doctor):
        url = reverse('api:doctors-list')
        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK
        assert len(res.data) >= 1
        assert res.data[0]['name'] == "Dr. Aris Thorne"
        assert res.data[0]['consultation_fee'] == 180

    def test_patient_book_and_cancel_appointment(self, api_client, patient_user, test_doctor):
        api_client.force_authenticate(user=patient_user)
        book_url = reverse('api:appointments-book')
        
        payload = {
            "doctor": test_doctor.id,
            "appointment_date": "2026-10-20",
            "time_slot": "10:00 AM - 10:45 AM",
            "reason": "Memory assessment"
        }
        
        # 1. Book appointment
        res = api_client.post(book_url, payload, format='json')
        assert res.status_code == status.HTTP_201_CREATED
        appt_id = res.data['id']
        assert res.data['status'] == 'Confirmed'
        assert res.data['doctor_name'] == 'Dr. Aris Thorne'
        
        # 2. List bookings
        my_bookings_url = reverse('api:appointments-my-bookings')
        res_list = api_client.get(my_bookings_url)
        assert res_list.status_code == status.HTTP_200_OK
        assert any(a['id'] == appt_id for a in res_list.data)
        
        # 3. Cancel appointment via POST
        cancel_url = reverse('api:appointments-cancel', kwargs={'pk': appt_id})
        res_cancel = api_client.post(cancel_url)
        assert res_cancel.status_code == status.HTTP_200_OK
        assert res_cancel.data['status'] == 'Cancelled'


@pytest.mark.django_db
class TestVRTasksREST:
    def test_patient_submit_and_delete_vr_task(self, api_client, patient_user):
        api_client.force_authenticate(user=patient_user)
        submit_url = reverse('api:vr_tasks_submit')
        
        payload = {
            "time_taken": 16.5,
            "errors": 1,
            "score": 90.0
        }
        
        res = api_client.post(submit_url, payload, format='json')
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data['cognitive_score'] == 27.0
        record_id = res.data['record']['id']
        
        # Patient profile cognitive score was updated
        patient_user.patient_profile.refresh_from_db()
        assert patient_user.patient_profile.cognitive_score == 27.0
        
        # Delete VR record via POST /vr-tasks/<id>/delete/
        delete_url = reverse('api:vr_tasks_delete', kwargs={'pk': record_id})
        res_del = api_client.post(delete_url)
        assert res_del.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestPredictionsDetailAndPOSTDelete:
    def test_prediction_post_delete(self, api_client, patient_user):
        prediction = PredictionRecord.objects.create(
            patient=patient_user.patient_profile,
            input_features={"age": 65, "cognitive_score": 28.0},
            prediction_class="Normal",
            probability=0.12,
            model_version="v1.0"
        )
        api_client.force_authenticate(user=patient_user)
        
        # Detail view
        detail_url = reverse('api:patient_prediction_detail', kwargs={'pk': prediction.id})
        res = api_client.get(detail_url)
        assert res.status_code == status.HTTP_200_OK
        assert res.data['prediction_class'] == 'Normal'
        
        # Delete via POST
        delete_post_url = reverse('api:predict_delete', kwargs={'pk': prediction.id})
        res_del = api_client.post(delete_post_url)
        assert res_del.status_code == status.HTTP_200_OK
        assert not PredictionRecord.objects.filter(id=prediction.id).exists()


@pytest.mark.django_db
class TestModelArtifactActivation:
    def test_activate_model_artifact(self, api_client, manager_user):
        from training.models import TrainedModelArtifact
        m1 = TrainedModelArtifact.objects.create(
            name="Model-Old",
            model_type="Random Forest",
            hyperparameters={"n_estimators": 50},
            metrics={"final_accuracy": 0.90, "final_loss": 0.10},
            is_active=True
        )
        m2 = TrainedModelArtifact.objects.create(
            name="Model-New",
            model_type="Deep Learning MLP",
            hyperparameters={"epochs": 10},
            metrics={"final_accuracy": 0.93, "final_loss": 0.07},
            is_active=False
        )
        
        api_client.force_authenticate(user=manager_user)
        activate_url = reverse('api:training_models_activate', kwargs={'pk': m2.id})
        res = api_client.post(activate_url)
        assert res.status_code == status.HTTP_200_OK
        assert res.data['status'] == 'ACTIVATED'
        
        m1.refresh_from_db()
        m2.refresh_from_db()
        assert m1.is_active is False
        assert m2.is_active is True


@pytest.mark.django_db
class TestChatbotRAGREST:
    def test_chatbot_query_general(self, api_client):
        url = reverse('api:chatbot_query')
        payload = {"message": "What is an MMSE score?"}
        res = api_client.post(url, payload, format='json')
        assert res.status_code == status.HTTP_200_OK
        assert "MMSE" in res.data['response']
        assert len(res.data['retrieved_sources']) >= 1
        assert len(res.data['actions']) >= 1

    def test_chatbot_query_appointment_intent(self, api_client):
        url = reverse('api:chatbot_query')
        payload = {"message": "I want to schedule an appointment with a neurologist"}
        res = api_client.post(url, payload, format='json')
        assert res.status_code == status.HTTP_200_OK
        assert res.data['intent'] == "book_appointment"
        assert any(a['url'] == '/appointments/book/' for a in res.data['actions'])


class TestPrescriptionAdvisorUnit:
    def test_prescription_advisor_analysis(self):
        from prescription_advisor import PrescriptionAdvisor
        advisor = PrescriptionAdvisor()
        text = "Rx: Patient Bob. Donepezil 10mg once daily at bedtime. Memantine 10mg twice daily."
        report = advisor.analyze_prescription(text)
        assert report['detected_drugs_count'] == 2
        assert any(d['generic_name'].startswith('Donepezil') for d in report['detected_drugs'])
        assert len(report['interaction_alerts']) >= 1
        assert "Beneficial Synergistic Combination" in report['interaction_alerts'][0]['severity']



