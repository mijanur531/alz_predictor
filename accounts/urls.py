from django.urls import path
from .views import (
    HomeView,
    CustomLoginView,
    CustomLogoutView,
    RegisterView,
    PatientDashboardView,
    ServiceDashboardView,
    ManagementDashboardView,
    AboutView,
    ContactView,
    VRTaskView
)

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    
    # Dashboards
    path('dashboard/', PatientDashboardView.as_view(), name='patient_dashboard'),
    path('dashboard/vr-test/', VRTaskView.as_view(), name='vr_test'),
    path('service/dashboard/', ServiceDashboardView.as_view(), name='service_dashboard'),
    path('management/dashboard/', ManagementDashboardView.as_view(), name='management_dashboard'),
    
    # Pages
    path('about/', AboutView.as_view(), name='about'),
    path('contact/', ContactView.as_view(), name='contact'),
]
