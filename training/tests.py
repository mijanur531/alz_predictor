import pytest
from django.urls import reverse
from accounts.models import User
from training.models import TrainedModelArtifact

@pytest.fixture
def patient_user(db):
    return User.objects.create_user(username="patient_charlie", password="password123", role="patient")

@pytest.fixture
def manager_user(db):
    return User.objects.create_user(username="manager_charlie", password="password123", role="management")

@pytest.mark.django_db
class TestModelTrainingDashboard:
    def test_training_restricted_to_management(self, client, patient_user):
        client.force_login(patient_user)
        url = reverse('model_training_dashboard')
        res = client.get(url)
        assert res.status_code == 302 # Redirected

    def test_manager_can_access_training(self, client, manager_user):
        client.force_login(manager_user)
        url = reverse('model_training_dashboard')
        res = client.get(url)
        assert res.status_code == 200

    def test_trigger_model_training(self, client, manager_user, mocker):
        client.force_login(manager_user)
        url = reverse('model_training_dashboard')
        
        # Test training post triggers Celery task
        # Because CELERY_TASK_ALWAYS_EAGER = True in dev.py, it executes synchronously and creates the artifact
        payload = {
            "model_type": "Random Forest",
            "epochs": 4,
            "n_estimators": 50,
            "max_depth": 5
        }
        
        res = client.post(url, payload, content_type='application/json')
        assert res.status_code == 200
        assert res.json()['status'] == 'STARTED'
        
        # Verify active model created
        artifact = TrainedModelArtifact.objects.filter(is_active=True).first()
        assert artifact is not None
        assert artifact.model_type == "Random Forest"
        assert artifact.metrics["final_accuracy"] > 0.0
        assert len(artifact.metrics["loss_curve"]) == 4
