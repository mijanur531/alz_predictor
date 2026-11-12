from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView,
    CurrentUserView,
    CSRFTokenView,
    JWTLoginView,
    JWTLogoutView,
    ChatbotQueryView,
    PatientPredictionsView,
    PatientPredictionDetailView,
    PredictTriggerView,
    PredictStatusView,
    DoctorViewSet,
    AppointmentViewSet,
    VRTaskViewSet,
    PrescriptionScanViewSet,
    ModelTrainingViewSet,
    ServiceCasesView,
    ServiceReviewCaseView,
    ManagementStatsView,
    ContactSubmitView,
)

app_name = 'api'

router = DefaultRouter()
router.register('doctors', DoctorViewSet, basename='doctors')
router.register('appointments', AppointmentViewSet, basename='appointments')
router.register('vr-tasks', VRTaskViewSet, basename='vr-tasks')
router.register('prescriptions', PrescriptionScanViewSet, basename='prescriptions')
router.register('training', ModelTrainingViewSet, basename='training')

urlpatterns = [
    # Auth Endpoints
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/csrf/', CSRFTokenView.as_view(), name='csrf_token'),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('auth/jwt-login/', JWTLoginView.as_view(), name='jwt_login'),
    path('auth/jwt-logout/', JWTLogoutView.as_view(), name='jwt_logout'),
    path('auth/me/', CurrentUserView.as_view(), name='current_user'),
    path('chatbot/query/', ChatbotQueryView.as_view(), name='chatbot_query'),
    
    # Patient Predictions
    path('patients/me/predictions/', PatientPredictionsView.as_view(), name='patient_predictions'),
    path('patients/me/predictions/<int:pk>/', PatientPredictionDetailView.as_view(), name='patient_prediction_detail'),
    path('predict/', PredictTriggerView.as_view(), name='predict_trigger'),
    path('predict/status/<str:task_id>/', PredictStatusView.as_view(), name='predict_status'),
    path('predict/<int:pk>/delete/', PatientPredictionDetailView.as_view(), name='predict_delete'),
    
    # Appointments Specific Endpoints
    path('appointments/doctors/', DoctorViewSet.as_view({'get': 'list'}), name='appointments_doctors'),
    path('appointments/book/', AppointmentViewSet.as_view({'post': 'create'}), name='appointments_book'),
    path('appointments/my-bookings/', AppointmentViewSet.as_view({'get': 'list'}), name='appointments_my_bookings'),
    path('appointments/<int:pk>/cancel/', AppointmentViewSet.as_view({'post': 'cancel', 'delete': 'cancel'}), name='appointments_cancel'),
    
    # VR Tasks Specific Endpoints
    path('vr-tasks/submit/', VRTaskViewSet.as_view({'post': 'create'}), name='vr_tasks_submit'),
    path('vr-tasks/history/', VRTaskViewSet.as_view({'get': 'list'}), name='vr_tasks_history'),
    path('vr-tasks/<int:pk>/delete/', VRTaskViewSet.as_view({'post': 'post_delete'}), name='vr_tasks_delete'),

    # Prescriptions Specific Endpoints
    path('prescriptions/<int:pk>/delete/', PrescriptionScanViewSet.as_view({'post': 'post_delete'}), name='prescriptions_delete'),

    # Model Training Specific Endpoints
    path('training/train/', ModelTrainingViewSet.as_view({'post': 'create'}), name='training_train'),
    path('training/models/', ModelTrainingViewSet.as_view({'get': 'list'}), name='training_models_list'),
    path('training/models/<int:pk>/activate/', ModelTrainingViewSet.as_view({'post': 'activate_model'}), name='training_models_activate'),

    # Service Provider Actions
    path('service/cases/', ServiceCasesView.as_view(), name='service_cases'),
    path('service/cases/<int:pk>/review/', ServiceReviewCaseView.as_view(), name='service_review_case'),
    
    # Management Analytics
    path('management/stats/', ManagementStatsView.as_view(), name='management_stats'),
    
    # Contact Message Form & History
    path('contact/', ContactSubmitView.as_view(), name='contact_submit'),
    
    # Router inclusions
    path('', include(router.urls)),
]

