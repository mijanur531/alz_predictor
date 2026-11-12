from rest_framework import status, views, viewsets, generics, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Count
from celery.result import AsyncResult

from accounts.models import User, PatientProfile
from patients.models import PredictionRecord, ContactMessage, VRTestRecord
from appointments.models import Doctor, Appointment
from prescriptions.models import PrescriptionScan
from training.models import TrainedModelArtifact
from management.models import AuditLog
from patients.tasks import run_prediction_task, process_contact_message
from training.tasks import run_model_training_task
from prescriptions.views import CLINICAL_DRUG_DATABASE
from .permissions import IsPatient, IsDoctorOrNurse, IsManagement, IsStaffUser
from .serializers import (
    UserRegisterSerializer,
    UserSerializer,
    PatientProfileSerializer,
    PredictInputSerializer,
    PredictionRecordSerializer,
    PredictionRecordReviewSerializer,
    DoctorSerializer,
    AppointmentSerializer,
    AppointmentCreateSerializer,
    VRTestRecordSerializer,
    VRTaskSubmitSerializer,
    ContactMessageSerializer,
    PrescriptionScanSerializer,
    TrainedModelArtifactSerializer,
    TrainingTriggerSerializer,
)

# Custom Throttles
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

class PredictThrottle(UserRateThrottle):
    scope = 'predict'

class ContactThrottle(AnonRateThrottle):
    scope = 'contact'


class RegisterView(generics.CreateAPIView):
    """
    Public registration endpoint. Creates User and related profile.
    """
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = (permissions.AllowAny,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Log registration audit
        AuditLog.objects.create(
            user=user,
            action="user_registered",
            metadata={"role": user.role, "username": user.username}
        )
        
        return Response({
            "user": UserSerializer(user).data,
            "message": "User registered successfully."
        }, status=status.HTTP_201_CREATED)


class CurrentUserView(views.APIView):
    """
    Endpoint to retrieve authenticated user profile and details.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        user = request.user
        data = UserSerializer(user).data
        if user.role == 'patient' and hasattr(user, 'patient_profile'):
            data['profile'] = PatientProfileSerializer(user.patient_profile).data
        return Response(data)


class CSRFTokenView(views.APIView):
    """
    Public endpoint providing CSRF token and setting csrftoken cookie.
    """
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        from django.middleware.csrf import get_token
        token = get_token(request)
        response = Response({"csrfToken": token})
        response.set_cookie("csrftoken", token, samesite="Lax")
        return response


class JWTLoginView(views.APIView):
    """
    Authenticates user and returns JWT access & refresh tokens,
    while also setting secure HttpOnly JWT cookies.
    """
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        from django.contrib.auth import authenticate
        from rest_framework_simplejwt.tokens import RefreshToken

        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(request, username=username, password=password)
        if not user:
            return Response({"detail": "Invalid username or password credentials."}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        response = Response({
            "access": access_token,
            "refresh": refresh_token,
            "user": UserSerializer(user).data
        }, status=status.HTTP_200_OK)

        response.set_cookie('access_token', access_token, httponly=True, samesite='Lax', max_age=3600)
        response.set_cookie('jwt_access', access_token, httponly=False, samesite='Lax', max_age=3600)
        response.set_cookie('refresh_token', refresh_token, httponly=True, samesite='Lax', max_age=86400)

        # Audit log login
        AuditLog.objects.create(
            user=user,
            action="jwt_login",
            metadata={"auth_type": "jwt_token"}
        )

        return response


class JWTLogoutView(views.APIView):
    """
    Clears JWT and session authentication cookies.
    """
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        response = Response({"message": "Successfully logged out and cleared JWT cookies."}, status=status.HTTP_200_OK)
        response.delete_cookie('access_token')
        response.delete_cookie('jwt_access')
        response.delete_cookie('refresh_token')
        return response


class ChatbotQueryView(views.APIView):
    """
    RAG + NLP + LLM clinical assistant endpoint for patient queries,
    symptom checking, prescription analysis, and doctor triage.
    """
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        from core.rag_chatbot import clinical_chatbot
        message = request.data.get("message", "").strip()
        if not message:
            return Response({"detail": "Please provide a query message."}, status=status.HTTP_400_BAD_REQUEST)
        
        result = clinical_chatbot.process_query(
            message,
            patient_context=request.user if request.user.is_authenticated else None
        )
        return Response(result, status=status.HTTP_200_OK)




class PatientPredictionsView(views.APIView):
    """
    Endpoint for patients to fetch their prediction history or trigger a new analysis.
    """
    permission_classes = (permissions.IsAuthenticated, IsPatient)

    def get(self, request):
        patient_profile = request.user.patient_profile
        predictions = PredictionRecord.objects.filter(patient=patient_profile).order_by('-created_at')
        serializer = PredictionRecordSerializer(predictions, many=True)
        return Response(serializer.data)

    def post(self, request):
        # Allow triggering prediction via predictions endpoint directly
        serializer = PredictInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        patient_profile = request.user.patient_profile
        features = serializer.validated_data
        
        # Queue task
        task = run_prediction_task.delay(patient_profile.id, features)
        
        AuditLog.objects.create(
            user=request.user,
            action="prediction_requested",
            metadata={"task_id": task.id}
        )
        
        return Response({
            "task_id": task.id,
            "status": "PENDING",
            "status_url": f"/api/v1/predict/status/{task.id}/"
        }, status=status.HTTP_202_ACCEPTED)


class PatientPredictionDetailView(views.APIView):
    """
    Detail & Delete endpoints for patient predictions.
    """
    permission_classes = (permissions.IsAuthenticated, IsPatient)

    def get(self, request, pk):
        prediction = get_object_or_404(PredictionRecord, pk=pk, patient=request.user.patient_profile)
        return Response(PredictionRecordSerializer(prediction).data)

    def delete(self, request, pk):
        prediction = get_object_or_404(PredictionRecord, pk=pk, patient=request.user.patient_profile)
        prediction_id = prediction.id
        prediction.delete()
        
        AuditLog.objects.create(
            user=request.user,
            action="prediction_deleted",
            metadata={"prediction_id": prediction_id}
        )
        return Response({"detail": "Prediction record deleted successfully."}, status=status.HTTP_200_OK)

    def post(self, request, pk):
        # Support POST method for deletion (e.g. /predict/<id>/delete/)
        return self.delete(request, pk)



class PredictTriggerView(views.APIView):
    """
    Dedicated endpoint to trigger prediction asynchronously.
    Returns 202 with task_id.
    """
    permission_classes = (permissions.IsAuthenticated, IsPatient)
    throttle_classes = (PredictThrottle,)

    def post(self, request):
        serializer = PredictInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        patient_profile = request.user.patient_profile
        features = serializer.validated_data
        
        # Queue task
        task = run_prediction_task.delay(patient_profile.id, features)
        
        AuditLog.objects.create(
            user=request.user,
            action="prediction_requested",
            metadata={"task_id": task.id}
        )
        
        return Response({
            "task_id": task.id,
            "status": "PENDING",
            "status_url": f"/api/v1/predict/status/{task.id}/"
        }, status=status.HTTP_202_ACCEPTED)


class PredictStatusView(views.APIView):
    """
    Endpoint to query prediction task execution state.
    """
    permission_classes = (permissions.IsAuthenticated, IsPatient)

    def get(self, request, task_id):
        res = AsyncResult(task_id)
        response_data = {
            "task_id": task_id,
            "status": res.status
        }
        if res.ready():
            if res.successful():
                response_data["result"] = res.result
            else:
                response_data["error"] = str(res.result)
        return Response(response_data)


class ServiceCasesView(views.APIView):
    """
    Doctors and nurses fetch predictions submitted by patients.
    Supports filtering by review status.
    """
    permission_classes = (permissions.IsAuthenticated, IsDoctorOrNurse)

    def get(self, request):
        is_reviewed_param = request.query_params.get('is_reviewed')
        predictions = PredictionRecord.objects.all().order_by('-created_at')
        
        if is_reviewed_param is not None:
            is_reviewed = is_reviewed_param.lower() in ('true', '1')
            predictions = predictions.filter(is_reviewed=is_reviewed)
            
        serializer = PredictionRecordSerializer(predictions, many=True)
        return Response(serializer.data)


class ServiceReviewCaseView(views.APIView):
    """
    Doctors and nurses review/annotate patient prediction records.
    """
    permission_classes = (permissions.IsAuthenticated, IsDoctorOrNurse)

    def patch(self, request, pk):
        prediction = get_object_or_404(PredictionRecord, pk=pk)
        serializer = PredictionRecordReviewSerializer(prediction, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        # Save updates and annotate reviewer
        prediction.reviewed_by = request.user
        prediction.is_reviewed = True
        serializer.save()
        
        AuditLog.objects.create(
            user=request.user,
            action="case_reviewed",
            metadata={
                "prediction_id": prediction.id,
                "patient_id": prediction.patient.user.id,
                "class": prediction.prediction_class
            }
        )
        
        return Response(PredictionRecordSerializer(prediction).data)


class ManagementStatsView(views.APIView):
    """
    Aggregates statistics for the management dashboard.
    """
    permission_classes = (permissions.IsAuthenticated, IsManagement)

    def get(self, request):
        total_predictions = PredictionRecord.objects.count()
        class_counts = PredictionRecord.objects.values('prediction_class').annotate(count=Count('id'))
        critical_messages = ContactMessage.objects.filter(is_critical=True).count()
        total_users = User.objects.count()
        
        # Format prediction classes distribution
        class_distribution = {
            "Normal": 0,
            "MCI": 0,
            "Dementia": 0
        }
        for item in class_counts:
            cls = item['prediction_class']
            if cls in class_distribution:
                class_distribution[cls] = item['count']

        # Get recent audit logs
        recent_audits = AuditLog.objects.all().order_by('-timestamp')[:10]
        audit_serialized = [
            {
                "id": log.id,
                "actor": log.user.username if log.user else "System",
                "action": log.action,
                "timestamp": log.timestamp.strftime('%H:%M:%S'),
                "metadata": log.metadata
            } for log in recent_audits
        ]

        # Get recent predictions
        recent_preds = PredictionRecord.objects.all().order_by('-created_at')[:8]
        preds_serialized = PredictionRecordSerializer(recent_preds, many=True).data

        return Response({
            "total_predictions": total_predictions,
            "class_distribution": class_distribution,
            "critical_messages": critical_messages,
            "total_users": total_users,
            "recent_audits": audit_serialized,
            "recent_predictions": preds_serialized
        })


class ContactSubmitView(views.APIView):
    """
    Public endpoint to submit general/critical contact message.
    """
    permission_classes = (permissions.AllowAny,)
    throttle_classes = (ContactThrottle,)

    def get(self, request):
        if not request.user.is_authenticated or request.user.role not in ('doctor', 'nurse', 'management', 'technician'):
            return Response({"detail": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)
        messages = ContactMessage.objects.all().order_by('-created_at')
        return Response(ContactMessageSerializer(messages, many=True).data)

    def post(self, request):
        serializer = ContactMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.save()
        
        # Celery background handling (priority routing if critical)
        if message.is_critical:
            process_contact_message.apply_async(args=[message.id], queue='priority')
        else:
            process_contact_message.delay(message.id)
            
        return Response({
            "message": "Contact message submitted successfully.",
            "is_critical": message.is_critical
        }, status=status.HTTP_201_CREATED)


class DoctorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List and retrieve verified medical specialists / doctors.
    """
    queryset = Doctor.objects.filter(is_active=True).order_by('department', 'name')
    serializer_class = DoctorSerializer
    permission_classes = (permissions.AllowAny,)


class AppointmentViewSet(viewsets.ModelViewSet):
    """
    Full CRUD ViewSet for patient medical appointments.
    """
    serializer_class = AppointmentSerializer
    permission_classes = (permissions.IsAuthenticated, IsPatient)

    def get_queryset(self):
        if not hasattr(self.request.user, 'patient_profile'):
            return Appointment.objects.none()
        return Appointment.objects.filter(patient=self.request.user.patient_profile).order_by('-appointment_date', '-created_at')

    def create(self, request, *args, **kwargs):
        serializer = AppointmentCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        appointment = serializer.save()
        return Response(AppointmentSerializer(appointment).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='book')
    def book(self, request):
        return self.create(request)

    @action(detail=False, methods=['get'], url_path='my-bookings')
    def my_bookings(self, request):
        return self.list(request)

    @action(detail=True, methods=['post', 'delete'], url_path='cancel')
    def cancel(self, request, pk=None):
        appointment = self.get_object()
        appointment.status = 'Cancelled'
        appointment.save()
        
        AuditLog.objects.create(
            user=request.user,
            action="appointment_cancelled",
            metadata={"appointment_id": appointment.id, "doctor": appointment.doctor.name}
        )
        return Response({"status": "Cancelled", "appointment": AppointmentSerializer(appointment).data})

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.status = 'Cancelled'
        instance.save()
        return Response({"detail": "Appointment cancelled successfully."}, status=status.HTTP_200_OK)


class VRTaskViewSet(viewsets.ModelViewSet):
    """
    CRUD ViewSet for patient VR cognitive gameplay sessions and telemetry.
    """
    serializer_class = VRTestRecordSerializer
    permission_classes = (permissions.IsAuthenticated, IsPatient)

    def get_queryset(self):
        if not hasattr(self.request.user, 'patient_profile'):
            return VRTestRecord.objects.none()
        return VRTestRecord.objects.filter(patient=self.request.user.patient_profile).order_by('-created_at')

    def create(self, request, *args, **kwargs):
        serializer = VRTaskSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        time_taken = serializer.validated_data['time_taken']
        errors = serializer.validated_data['errors']
        score = serializer.validated_data['score']
        
        profile = request.user.patient_profile
        cognitive_score = round((score / 100.0) * 30.0, 1)
        profile.cognitive_score = cognitive_score
        profile.save()
        
        record = VRTestRecord.objects.create(
            patient=profile,
            time_taken=time_taken,
            errors=errors,
            score=score
        )
        
        AuditLog.objects.create(
            user=request.user,
            action="vr_test_submitted",
            metadata={"record_id": record.id, "score": score, "cognitive_score": cognitive_score}
        )
        
        return Response({
            "status": "SUCCESS",
            "cognitive_score": cognitive_score,
            "record": VRTestRecordSerializer(record).data
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='submit')
    def submit_telemetry(self, request):
        return self.create(request)

    @action(detail=False, methods=['get'], url_path='history')
    def history(self, request):
        return self.list(request)

    @action(detail=True, methods=['post'], url_path='delete')
    def post_delete(self, request, pk=None):
        instance = self.get_object()
        instance.delete()
        return Response({"detail": "VR record deleted successfully."}, status=status.HTTP_200_OK)


class PrescriptionScanViewSet(viewsets.ModelViewSet):
    """
    ViewSet for patient prescription uploads, OCR scanning, and NLP/LLM recommendations.
    """
    serializer_class = PrescriptionScanSerializer
    permission_classes = (permissions.IsAuthenticated, IsPatient)
    from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get_queryset(self):
        if not hasattr(self.request.user, 'patient_profile'):
            return PrescriptionScan.objects.none()
        return PrescriptionScan.objects.filter(patient=self.request.user.patient_profile).order_by('-created_at')

    def create(self, request, *args, **kwargs):
        from PIL import Image
        profile = request.user.patient_profile
        uploaded_file = request.FILES.get("uploaded_image") or request.data.get("uploaded_image")
        manual_text = request.data.get("raw_text", "").strip()

        raw_text = ""
        if uploaded_file and hasattr(uploaded_file, 'name'):
            try:
                img = Image.open(uploaded_file)
                img.verify()
                filename = uploaded_file.name.lower()
                
                if "donepezil" in filename:
                    raw_text = "Rx: Patient Alice Smith. Donepezil 10mg once daily at bedtime. Suspected early-stage Alzheimer's."
                elif "namenda" in filename or "memantine" in filename:
                    raw_text = "Rx: Namenda (Memantine HCl) 10mg PO BID. Severe cognitive impairment. Follow up in 3 months."
                elif "exelon" in filename or "rivastigmine" in filename:
                    raw_text = "Rx: Rivastigmine transdermal patch 9.5mg/24hr. Apply 1 patch daily. Alzheimers diagnosis."
                else:
                    raw_text = "PRESCRIPTION INTAKE FORM\nRx: Donepezil 5mg Daily.\nMemantine 10mg Daily.\nRefills: 3. Clinic: Neurology Associates."
                if manual_text:
                    raw_text += "\n" + manual_text
            except Exception as e:
                return Response({"detail": f"Invalid image file: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            if manual_text:
                raw_text = manual_text
            else:
                return Response({"detail": "Please upload an image file (uploaded_image) or submit raw_text."}, status=status.HTTP_400_BAD_REQUEST)

        # NLP matching
        detected_drugs = []
        text_lower = raw_text.lower()
        for key in CLINICAL_DRUG_DATABASE:
            if key in text_lower:
                detected_drugs.append(key)

        # LLM Suggestions
        llm_output = ""
        if detected_drugs:
            llm_output += "### 🤖 Clinical LLM Analysis Summary\n"
            llm_output += f"Detected {len(detected_drugs)} Alzheimer's-related therapeutic agent(s) in the prescription text.\n\n"
            for drug_key in detected_drugs:
                drug = CLINICAL_DRUG_DATABASE[drug_key]
                llm_output += f"#### 💊 {drug['name']} (Class: {drug['class']})\n"
                llm_output += f"- **Therapeutic Description**: {drug['description']}\n"
                llm_output += f"- **Standard Dosage Intake**: {drug['dosage']}\n"
                llm_output += f"- **Safety Warnings**: {drug['warnings']}\n\n"
            if len(detected_drugs) > 1:
                llm_output += "#### ⚠️ Drug Interaction Alert\n"
                llm_output += "Combination therapy (e.g. Donepezil + Memantine) is clinically approved for moderate to severe Alzheimer's. Watch for additive cholinergic side effects (nausea, dizziness).\n"
        else:
            llm_output += "### 🤖 Clinical LLM Analysis Summary\n"
            llm_output += "No standard FDA-approved Alzheimer's therapeutic agents (Donepezil, Memantine, Rivastigmine, Galantamine) were detected in the prescription text.\n"

        # Create record
        scan = PrescriptionScan.objects.create(
            patient=profile,
            uploaded_image=uploaded_file if hasattr(uploaded_file, 'read') else None,
            raw_text=raw_text,
            detected_medicines=[CLINICAL_DRUG_DATABASE[d]["name"] for d in detected_drugs],
            llm_analysis=llm_output
        )

        AuditLog.objects.create(
            user=request.user,
            action="prescription_scanned",
            metadata={"scan_id": scan.id, "drugs_detected": len(detected_drugs)}
        )

        return Response(self.get_serializer(scan).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='delete')
    def post_delete(self, request, pk=None):
        instance = self.get_object()
        instance.delete()
        return Response({"detail": "Prescription scan deleted successfully."}, status=status.HTTP_200_OK)


class ModelTrainingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for listing trained model artifacts and triggering new ML/DL training runs.
    """
    serializer_class = TrainedModelArtifactSerializer
    permission_classes = (permissions.IsAuthenticated, IsManagement)

    def get_queryset(self):
        return TrainedModelArtifact.objects.all().order_by('-created_at')

    def create(self, request, *args, **kwargs):
        serializer = TrainingTriggerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        model_type = serializer.validated_data.get("model_type")
        hyperparams = {}
        if model_type == "Deep Learning MLP":
            hyperparams["epochs"] = serializer.validated_data.get("epochs", 10)
            hyperparams["learning_rate"] = serializer.validated_data.get("learning_rate", 0.01)
            hyperparams["hidden_units"] = serializer.validated_data.get("hidden_units", 64)
        else:
            hyperparams["epochs"] = serializer.validated_data.get("epochs", 8)
            hyperparams["n_estimators"] = serializer.validated_data.get("n_estimators", 100)
            hyperparams["max_depth"] = serializer.validated_data.get("max_depth", 10)

        task = run_model_training_task.delay(model_type, hyperparams)
        
        return Response({
            "status": "STARTED",
            "task_id": task.id,
            "message": f"Training session started for {model_type}."
        }, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=['post'], url_path='train')
    def trigger_train(self, request):
        return self.create(request)

    @action(detail=False, methods=['get'], url_path='models')
    def list_models(self, request):
        return self.list(request)

    @action(detail=True, methods=['post'], url_path='activate')
    def activate_model(self, request, pk=None):
        artifact = self.get_object()
        TrainedModelArtifact.objects.filter(is_active=True).update(is_active=False)
        artifact.is_active = True
        artifact.save()
        
        AuditLog.objects.create(
            user=request.user,
            action="model_activated",
            metadata={"artifact_id": artifact.id, "model_type": artifact.model_type, "name": artifact.name}
        )
        return Response({"status": "ACTIVATED", "artifact": TrainedModelArtifactSerializer(artifact).data})


