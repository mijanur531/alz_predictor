import pytest
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.models import User
from prescriptions.models import PrescriptionScan
from io import BytesIO
from PIL import Image

@pytest.fixture
def patient_user(db):
    user = User.objects.create_user(username="patient_bob", password="password123", role="patient")
    return user

@pytest.fixture
def doctor_user(db):
    return User.objects.create_user(username="doctor_bob", password="password123", role="doctor")

@pytest.mark.django_db
class TestPrescriptionScanner:
    def test_scanner_page_restricted_to_patients(self, client, doctor_user):
        client.force_login(doctor_user)
        url = reverse('prescriptions_scanner')
        res = client.get(url)
        # Doctor redirected
        assert res.status_code == 302

    def test_patient_can_access_scanner(self, client, patient_user):
        client.force_login(patient_user)
        url = reverse('prescriptions_scanner')
        res = client.get(url)
        assert res.status_code == 200

    def test_text_prescription_intake(self, client, patient_user):
        client.force_login(patient_user)
        url = reverse('prescriptions_scanner')
        
        payload = {
            "raw_text": "Rx: Donepezil 5mg daily for Alzheimer's."
        }
        res = client.post(url, payload)
        assert res.status_code == 302  # redirects on success
        
        # Verify scan saved and drug parsed
        scan = PrescriptionScan.objects.filter(patient=patient_user.patient_profile).first()
        assert scan is not None
        assert "Donepezil (Aricept)" in scan.detected_medicines
        assert "Donepezil" in scan.llm_analysis

    def test_image_prescription_intake(self, client, patient_user):
        client.force_login(patient_user)
        url = reverse('prescriptions_scanner')
        
        # Generate a small valid image in-memory using Pillow
        file_io = BytesIO()
        image = Image.new('RGB', (100, 100), color='white')
        image.save(file_io, 'JPEG')
        file_io.seek(0)
        
        img_file = SimpleUploadedFile("prescription_donepezil.jpg", file_io.read(), content_type="image/jpeg")
        
        payload = {
            "prescription_image": img_file,
            "raw_text": ""
        }
        res = client.post(url, payload)
        assert res.status_code == 302
        
        scan = PrescriptionScan.objects.filter(patient=patient_user.patient_profile).first()
        assert scan is not None
        assert "Donepezil (Aricept)" in scan.detected_medicines
