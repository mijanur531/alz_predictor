import os
import datetime
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alz_predictor.settings.dev')
django.setup()

from accounts.models import User, PatientProfile, ServiceProviderProfile
from patients.models import PredictionRecord, ContactMessage, VRTestRecord
from appointments.models import Doctor, Appointment
from prescriptions.models import PrescriptionScan
from training.models import TrainedModelArtifact
from management.models import AuditLog

def seed_data():
    print("Seeding AlzPredictor database...")
    
    # 1. Create Management Users
    manager, created = User.objects.get_or_create(
        username="manager",
        defaults={
            "email": "manager@alzpredictor.com",
            "role": "management",
            "first_name": "Sarah",
            "last_name": "Jenkins"
        }
    )
    if created:
        manager.set_password("password123")
        manager.save()
        print("Created management user: manager / password123")
    
    # 2. Create Doctors & Staff Users
    doctor_user, created = User.objects.get_or_create(
        username="doctor_house",
        defaults={
            "email": "house@alzpredictor.com",
            "role": "doctor",
            "first_name": "Gregory",
            "last_name": "House"
        }
    )
    if created:
        doctor_user.set_password("password123")
        doctor_user.save()
        profile = doctor_user.provider_profile
        profile.department = "Neurology"
        profile.qualification = "MD, Board Certified Neurologist"
        profile.save()
        print("Created doctor user: doctor_house / password123")

    nurse_user, created = User.objects.get_or_create(
        username="nurse_clara",
        defaults={
            "email": "clara@alzpredictor.com",
            "role": "nurse",
            "first_name": "Clara",
            "last_name": "Barton"
        }
    )
    if created:
        nurse_user.set_password("password123")
        nurse_user.save()
        profile = nurse_user.provider_profile
        profile.department = "Geriatrics"
        profile.qualification = "BSN, Certified Geriatric Nurse"
        profile.save()
        print("Created nurse user: nurse_clara / password123")

    # 3. Create Verified Doctor Directory
    doctors_data = [
        {
            "name": "Dr. Aris Thorne",
            "specialty": "Neuro-Geriatric Cognitive Specialist",
            "department": "Neurology",
            "qualification": "MD, PhD - Harvard Medical School",
            "experience_years": 16,
            "rating": 4.98,
            "consultation_fee": 180,
            "avatar_url": "https://images.unsplash.com/photo-1622253692010-333f2da6031d?auto=format&fit=crop&w=400&q=80",
            "email": "aris.thorne@alzpredictor.com",
            "phone": "+1 (555) 234-5678",
            "bio": "Specializes in early-stage biomarker identification, amyloid plaque PET interpretation, and digital cognitive therapy.",
            "available_days": "Mon, Tue, Wed, Thu, Fri",
            "available_hours": "09:00 AM - 05:00 PM"
        },
        {
            "name": "Dr. Elena Rostova",
            "specialty": "Cognitive Memory & Dementia Consultant",
            "department": "Geriatrics",
            "qualification": "MD - Johns Hopkins University",
            "experience_years": 12,
            "rating": 4.92,
            "consultation_fee": 160,
            "avatar_url": "https://images.unsplash.com/photo-1594824813590-77a8be65cf72?auto=format&fit=crop&w=400&q=80",
            "email": "elena.rostova@alzpredictor.com",
            "phone": "+1 (555) 345-6789",
            "bio": "Pioneer in multi-modal rehabilitation and holistic memory preservation for elder patients.",
            "available_days": "Mon, Wed, Fri",
            "available_hours": "08:30 AM - 04:30 PM"
        },
        {
            "name": "Dr. Marcus Vance",
            "specialty": "Vascular Neurology & Cerebrovascular Health",
            "department": "Cardiology",
            "qualification": "MD, FACC - Stanford University",
            "experience_years": 19,
            "rating": 4.95,
            "consultation_fee": 210,
            "avatar_url": "https://images.unsplash.com/photo-1537368910025-700350fe46c7?auto=format&fit=crop&w=400&q=80",
            "email": "marcus.vance@alzpredictor.com",
            "phone": "+1 (555) 456-7890",
            "bio": "Investigates cardiovascular flow interplay with cognitive decline and microvascular pathology.",
            "available_days": "Tue, Thu, Sat",
            "available_hours": "10:00 AM - 06:00 PM"
        },
        {
            "name": "Dr. Sophia Lin",
            "specialty": "Gut-Brain Axis & Metabolic Neurology",
            "department": "Gastroenterology",
            "qualification": "MD - UCSF School of Medicine",
            "experience_years": 9,
            "rating": 4.88,
            "consultation_fee": 145,
            "avatar_url": "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?auto=format&fit=crop&w=400&q=80",
            "email": "sophia.lin@alzpredictor.com",
            "phone": "+1 (555) 567-8901",
            "bio": "Researches gut microbiome influence on neuro-inflammatory cascades in aging brains.",
            "available_days": "Mon, Tue, Thu",
            "available_hours": "09:00 AM - 03:00 PM"
        },
        {
            "name": "Dr. David Sterling",
            "specialty": "Preventative Internal Medicine & Longevity",
            "department": "General Medicine",
            "qualification": "MD, MPH - Oxford University",
            "experience_years": 14,
            "rating": 4.91,
            "consultation_fee": 130,
            "avatar_url": "https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?auto=format&fit=crop&w=400&q=80",
            "email": "david.sterling@alzpredictor.com",
            "phone": "+1 (555) 678-9012",
            "bio": "Focuses on comprehensive routine diagnostics, blood lipid profiling, and lifelong lifestyle coaching.",
            "available_days": "Mon, Tue, Wed, Thu, Fri",
            "available_hours": "08:00 AM - 05:00 PM"
        }
    ]

    doctor_objs = []
    for doc in doctors_data:
        obj, _ = Doctor.objects.update_or_create(
            name=doc["name"],
            defaults=doc
        )
        doctor_objs.append(obj)
    print(f"Seeded {len(doctor_objs)} verified specialist doctors.")

    # 4. Create Patients
    patient_user, created = User.objects.get_or_create(
        username="patient_alice",
        defaults={
            "email": "alice@gmail.com",
            "role": "patient",
            "first_name": "Alice",
            "last_name": "Smith"
        }
    )
    if created:
        patient_user.set_password("password123")
        patient_user.save()
        p_profile = patient_user.patient_profile
        p_profile.age = 76
        p_profile.gender = "Female"
        p_profile.education_level = "Bachelor's"
        p_profile.bmi = 22.4
        p_profile.smoking = False
        p_profile.cognitive_score = 18.5
        p_profile.family_history = True
        p_profile.physical_activity = 1.5
        p_profile.save()
        print("Created patient user: patient_alice / password123")

    alice_profile = patient_user.patient_profile

    # 5. Create Mock Predictions for Alice
    if not PredictionRecord.objects.filter(patient=alice_profile).exists():
        # Prediction 1: Dementia (unreviewed)
        PredictionRecord.objects.create(
            patient=alice_profile,
            input_features={
                "age": 76,
                "gender": "Female",
                "education_level": "Bachelor's",
                "bmi": 22.4,
                "cognitive_score": 18.5,
                "family_history": True,
                "physical_activity": 1.5,
                "smoking": False
            },
            prediction_class="Dementia",
            probability=0.68,
            model_version="v1.2.0-rf-ensemble",
            is_reviewed=False
        )
        # Prediction 2: MCI (reviewed)
        PredictionRecord.objects.create(
            patient=alice_profile,
            input_features={
                "age": 76,
                "gender": "Female",
                "education_level": "Bachelor's",
                "bmi": 22.4,
                "cognitive_score": 23.0,
                "family_history": True,
                "physical_activity": 4.0,
                "smoking": False
            },
            prediction_class="MCI",
            probability=0.32,
            model_version="v1.2.0-rf-ensemble",
            reviewed_by=doctor_user,
            review_comments="Intake MMSE score represents early stage cognitive deficits. Scheduled brain MRI and digital VR monitoring.",
            is_reviewed=True
        )
        print("Created initial clinical prediction records.")

    # 6. Create VR Test Records
    if not VRTestRecord.objects.filter(patient=alice_profile).exists():
        VRTestRecord.objects.create(
            patient=alice_profile,
            time_taken=18.4,
            errors=2,
            score=78.0
        )
        VRTestRecord.objects.create(
            patient=alice_profile,
            time_taken=14.2,
            errors=1,
            score=86.5
        )
        print("Created sample VR cognitive test records.")

    # 7. Create Prescription Scans
    if not PrescriptionScan.objects.filter(patient=alice_profile).exists():
        PrescriptionScan.objects.create(
            patient=alice_profile,
            raw_text="Rx: Patient Alice Smith. Donepezil 10mg once daily at bedtime. Memantine 10mg PO BID.",
            detected_medicines=["Donepezil (Aricept)", "Memantine (Namenda)"],
            llm_analysis="### 🤖 Clinical LLM Analysis Summary\nDetected 2 Alzheimer's-related therapeutic agent(s).\n\n#### 💊 Donepezil (Aricept) (Class: Acetylcholinesterase Inhibitor)\n- **Therapeutic Description**: Improves cognitive function by increasing brain acetylcholine levels.\n- **Standard Dosage**: 5mg - 10mg once daily at bedtime.\n\n#### 💊 Memantine (Namenda) (Class: NMDA Receptor Antagonist)\n- **Therapeutic Description**: Protects neural tissue against pathological glutamate excitotoxicity.\n- **Standard Dosage**: 10mg twice daily PO.\n\n#### ⚠️ Drug Interaction Alert\nCombination therapy is clinically approved for moderate to severe Alzheimer's."
        )
        print("Created sample prescription scan record.")

    # 8. Create Appointments
    today = datetime.date.today()
    if not Appointment.objects.filter(patient=alice_profile).exists():
        Appointment.objects.create(
            patient=alice_profile,
            doctor=doctor_objs[0],  # Dr. Aris Thorne
            appointment_date=today + datetime.timedelta(days=3),
            time_slot="10:00 AM - 10:45 AM",
            reason="Follow-up on MMSE score decline and memory recall assessment.",
            status="Confirmed"
        )
        Appointment.objects.create(
            patient=alice_profile,
            doctor=doctor_objs[1],  # Dr. Elena Rostova
            appointment_date=today + datetime.timedelta(days=10),
            time_slot="02:30 PM - 03:15 PM",
            reason="Routine geriatric cognitive review and lifestyle plan.",
            status="Scheduled"
        )
        print("Created initial medical appointment bookings.")

    # 9. Create Trained Model Artifacts
    if not TrainedModelArtifact.objects.exists():
        TrainedModelArtifact.objects.create(
            name="RF-RandomForest-Classifier-2026",
            model_type="Random Forest",
            hyperparameters={"n_estimators": 100, "max_depth": 10, "epochs": 8},
            metrics={"final_accuracy": 0.942, "final_loss": 0.084, "precision": 0.931, "recall": 0.952},
            is_active=True
        )
        TrainedModelArtifact.objects.create(
            name="MLP-DeepNeuralNet-v1.4",
            model_type="Deep Learning MLP",
            hyperparameters={"epochs": 12, "learning_rate": 0.005, "hidden_units": 128},
            metrics={"final_accuracy": 0.918, "final_loss": 0.124, "precision": 0.905, "recall": 0.928},
            is_active=False
        )
        print("Created trained model artifacts.")

    # 10. Create Contact Messages & Audit Logs
    ContactMessage.objects.get_or_create(
        name="Support Request",
        email="support@client.com",
        message="Cannot access the REST API with my JWT token. Help requested.",
        is_critical=False
    )
    ContactMessage.objects.get_or_create(
        name="Critical Alert System test",
        email="onsite-tech@alzpredictor.com",
        message="Emergency technical maintenance alert. High database loads detected.",
        is_critical=True
    )

    AuditLog.objects.create(user=None, action="system_initialized", metadata={"version": "2.0.0", "theme": "Nuvica"})
    AuditLog.objects.create(user=manager, action="dashboard_accessed")
    AuditLog.objects.create(user=doctor_user, action="case_reviewed", metadata={"prediction_id": 2})

    print("[SUCCESS] Comprehensive database seeding completed successfully!")

if __name__ == "__main__":
    seed_data()

