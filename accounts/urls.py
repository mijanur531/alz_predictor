from django.contrib.auth import views as auth_views
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
    VRTaskView,
    JWTTokenPageView,
)

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('accounts/login/', CustomLoginView.as_view(), name='accounts_login'),
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='accounts/password_reset_form.html',
            email_template_name='accounts/password_reset_email.html',
            subject_template_name='accounts/password_reset_subject.txt',
        ),
        name='password_reset',
    ),
    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='accounts/password_reset_done.html',
        ),
        name='password_reset_done',
    ),
    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='accounts/password_reset_confirm.html',
        ),
        name='password_reset_confirm',
    ),
    path(
        'reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='accounts/password_reset_complete.html',
        ),
        name='password_reset_complete',
    ),
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
    path('api-token/', JWTTokenPageView.as_view(), name='api_token_page'),
]
