from rest_framework import serializers
from accounts.models import User, PatientProfile, ServiceProviderProfile
from patients.models import PredictionRecord, ContactMessage, VRTestRecord
from appointments.models import Doctor, Appointment
from prescriptions.models import PrescriptionScan
from training.models import TrainedModelArtifact

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'role', 'first_name', 'last_name')


class PatientProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientProfile
        fields = ('age', 'gender', 'education_level', 'bmi', 'smoking', 'cognitive_score', 'family_history', 'physical_activity')


class ServiceProviderProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceProviderProfile
        fields = ('department', 'qualification')


class UserRegisterSerializer(serializers.ModelSerializer):
    # Registration fields
    password = serializers.CharField(write_only=True, min_length=8)
    
    # Clinical profile optional fields (for patients)
    age = serializers.IntegerField(required=False, allow_null=True)
    gender = serializers.ChoiceField(choices=PatientProfile.GENDER_CHOICES, required=False, allow_null=True)
    education_level = serializers.ChoiceField(choices=PatientProfile.EDUCATION_CHOICES, required=False, allow_null=True)
    bmi = serializers.FloatField(required=False, allow_null=True)
    smoking = serializers.BooleanField(required=False, default=False)
    cognitive_score = serializers.FloatField(required=False, allow_null=True)
    family_history = serializers.BooleanField(required=False, default=False)
    physical_activity = serializers.FloatField(required=False, allow_null=True)
    
    # Staff profile optional fields (for doctor/nurse/technician)
    department = serializers.CharField(required=False, allow_null=True)
    qualification = serializers.CharField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'email', 'role', 'first_name', 'last_name',
                  'age', 'gender', 'education_level', 'bmi', 'smoking', 'cognitive_score',
                  'family_history', 'physical_activity', 'department', 'qualification')

    def validate(self, attrs):
        role = attrs.get('role', 'patient')
        if role == 'patient':
            # Optionally validate patient fields if needed
            pass
        return attrs

    def create(self, validated_data):
        # Extract profile fields
        profile_data = {
            'age': validated_data.pop('age', None),
            'gender': validated_data.pop('gender', None),
            'education_level': validated_data.pop('education_level', None),
            'bmi': validated_data.pop('bmi', None),
            'smoking': validated_data.pop('smoking', False),
            'cognitive_score': validated_data.pop('cognitive_score', None),
            'family_history': validated_data.pop('family_history', False),
            'physical_activity': validated_data.pop('physical_activity', None)
        }
        
        staff_data = {
            'department': validated_data.pop('department', 'General Medicine'),
            'qualification': validated_data.pop('qualification', 'General Staff')
        }

        # Create user (triggers signal to create default profile models)
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            role=validated_data.get('role', 'patient'),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )

        # Update the created profile with validated details
        if user.role == 'patient':
            profile = user.patient_profile
            for key, val in profile_data.items():
                setattr(profile, key, val)
            profile.save()
        else:
            profile = user.provider_profile
            for key, val in staff_data.items():
                setattr(profile, key, val)
            profile.save()

        return user


class PredictInputSerializer(serializers.Serializer):
    age = serializers.IntegerField(min_value=0, max_value=120)
    gender = serializers.ChoiceField(choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')])
    education_level = serializers.ChoiceField(choices=[("High School", "High School"), ("Bachelor's", "Bachelor's"), ("Master's", "Master's"), ("PhD", "PhD")])
    bmi = serializers.FloatField(min_value=10.0, max_value=60.0)
    smoking = serializers.BooleanField(default=False)
    cognitive_score = serializers.FloatField(min_value=0.0, max_value=30.0)
    family_history = serializers.BooleanField(default=False)
    physical_activity = serializers.FloatField(min_value=0.0, max_value=168.0)  # hours/week max


class PredictionRecordSerializer(serializers.ModelSerializer):
    patient_username = serializers.CharField(source='patient.user.username', read_only=True)
    patient_fullname = serializers.SerializerMethodField(read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.username', read_only=True)

    class Meta:
        model = PredictionRecord
        fields = ('id', 'patient', 'patient_username', 'patient_fullname', 'input_features', 
                  'prediction_class', 'probability', 'model_version', 
                  'reviewed_by', 'reviewed_by_name', 'review_comments', 'is_reviewed', 'created_at')
        read_only_fields = ('id', 'patient', 'prediction_class', 'probability', 'model_version', 'reviewed_by', 'created_at')

    def get_patient_fullname(self, obj):
        return obj.patient.user.get_full_name() or obj.patient.user.username


class PredictionRecordReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = PredictionRecord
        fields = ('review_comments', 'is_reviewed')
        extra_kwargs = {
            'review_comments': {'required': True},
            'is_reviewed': {'required': True}
        }


class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = ('id', 'name', 'specialty', 'department', 'qualification', 'experience_years',
                  'rating', 'consultation_fee', 'avatar_url', 'email', 'phone', 'bio', 'available_days',
                  'available_hours', 'is_active')


class AppointmentSerializer(serializers.ModelSerializer):
    patient_username = serializers.CharField(source='patient.user.username', read_only=True)
    patient_fullname = serializers.SerializerMethodField(read_only=True)
    doctor_name = serializers.CharField(source='doctor.name', read_only=True)
    doctor_specialty = serializers.CharField(source='doctor.specialty', read_only=True)
    doctor_department = serializers.CharField(source='doctor.department', read_only=True)
    doctor_avatar = serializers.CharField(source='doctor.avatar_url', read_only=True)

    class Meta:
        model = Appointment
        fields = ('id', 'patient', 'patient_username', 'patient_fullname', 'doctor',
                  'doctor_name', 'doctor_specialty', 'doctor_department', 'doctor_avatar',
                  'appointment_date', 'time_slot', 'reason', 'status', 'created_at', 'updated_at')
        read_only_fields = ('id', 'patient', 'created_at', 'updated_at')

    def get_patient_fullname(self, obj):
        return obj.patient.user.get_full_name() or obj.patient.user.username


class AppointmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ('doctor', 'appointment_date', 'time_slot', 'reason')

    def create(self, validated_data):
        patient = self.context['request'].user.patient_profile
        return Appointment.objects.create(patient=patient, status="Confirmed", **validated_data)


class VRTestRecordSerializer(serializers.ModelSerializer):
    patient_username = serializers.CharField(source='patient.user.username', read_only=True)
    cognitive_score_equivalent = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = VRTestRecord
        fields = ('id', 'patient', 'patient_username', 'time_taken', 'errors', 'score',
                  'cognitive_score_equivalent', 'created_at')
        read_only_fields = ('id', 'patient', 'created_at')

    def get_cognitive_score_equivalent(self, obj):
        return round((obj.score / 100.0) * 30.0, 1)


class VRTaskSubmitSerializer(serializers.Serializer):
    time_taken = serializers.FloatField(min_value=0.1)
    errors = serializers.IntegerField(min_value=0)
    score = serializers.FloatField(min_value=0.0, max_value=100.0)


class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ('id', 'name', 'email', 'message', 'is_critical', 'created_at')
        read_only_fields = ('id', 'created_at')


class PrescriptionScanSerializer(serializers.ModelSerializer):
    patient_username = serializers.CharField(source='patient.user.username', read_only=True)

    class Meta:
        model = PrescriptionScan
        fields = ('id', 'patient', 'patient_username', 'uploaded_image', 'raw_text', 'detected_medicines', 'llm_analysis', 'created_at')
        read_only_fields = ('id', 'patient', 'raw_text', 'detected_medicines', 'llm_analysis', 'created_at')


class TrainedModelArtifactSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainedModelArtifact
        fields = ('id', 'name', 'model_type', 'hyperparameters', 'metrics', 'is_active', 'created_at')
        read_only_fields = ('id', 'name', 'metrics', 'created_at')


class TrainingTriggerSerializer(serializers.Serializer):
    model_type = serializers.ChoiceField(choices=[('Random Forest', 'Random Forest'), ('Deep Learning MLP', 'Deep Learning MLP')])
    epochs = serializers.IntegerField(min_value=1, max_value=50, default=10)
    learning_rate = serializers.FloatField(required=False, min_value=0.0001, max_value=1.0)
    hidden_units = serializers.IntegerField(required=False, min_value=4, max_value=512)
    n_estimators = serializers.IntegerField(required=False, min_value=5, max_value=1000)
    max_depth = serializers.IntegerField(required=False, min_value=1, max_value=100)


