from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import TemplateView, CreateView, FormView, ListView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages

from accounts.models import User, PatientProfile
from patients.models import PredictionRecord, ContactMessage
from management.models import AuditLog
from patients.tasks import process_contact_message, run_prediction_task
from accounts.forms import UserRegisterForm, PatientIntakeForm, CaseReviewForm, ContactForm

class RoleRedirectMixin:
    """
    Redirects user after login based on their user role.
    """
    def get_success_url(self):
        user = self.request.user
        if user.role == 'patient':
            return reverse('patient_dashboard')
        elif user.role in ('doctor', 'nurse'):
            return reverse('service_dashboard')
        elif user.role == 'management':
            return reverse('management_dashboard')
        return reverse('home')


class HomeView(TemplateView):
    template_name = 'home.html'


class CustomLoginView(RoleRedirectMixin, LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.get_user()
        # Set user session info in Django cookies
        response.set_cookie('user_role', user.role, max_age=86400, samesite='Lax')
        response.set_cookie('username', user.username, max_age=86400, samesite='Lax')
        return response


class CustomLogoutView(LogoutView):
    next_page = 'home'
    
    def get(self, request, *args, **kwargs):
        from django.contrib.auth import logout as auth_logout
        if request.user.is_authenticated:
            AuditLog.objects.create(
                user=request.user,
                action="user_logged_out"
            )
        auth_logout(request)
        response = redirect(self.next_page)
        response.delete_cookie('user_role')
        response.delete_cookie('username')
        return response
        
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            AuditLog.objects.create(
                user=request.user,
                action="user_logged_out"
            )
        response = super().dispatch(request, *args, **kwargs)
        response.delete_cookie('user_role')
        response.delete_cookie('username')
        return response


class RegisterView(CreateView):
    form_class = UserRegisterForm
    template_name = 'accounts/register.html'
    
    def get_success_url(self):
        user = self.object
        if user.role == 'patient':
            return reverse('patient_dashboard')
        elif user.role in ('doctor', 'nurse'):
            return reverse('service_dashboard')
        elif user.role == 'management':
            return reverse('management_dashboard')
        return reverse('home')

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.object
        login(self.request, user)  # Auto login after signup
        
        # Set cookies
        response.set_cookie('user_role', user.role, max_age=86400, samesite='Lax')
        response.set_cookie('username', user.username, max_age=86400, samesite='Lax')

        # Audit log on register
        AuditLog.objects.create(
            user=user,
            action="user_registered",
            metadata={"role": user.role}
        )
        return response



# Role Guard Mixins
class PatientRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'patient'
    def handle_no_permission(self):
        messages.error(self.request, "Access Denied: Patient role required.")
        return redirect('home')

class DoctorNurseRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in ('doctor', 'nurse')
    def handle_no_permission(self):
        messages.error(self.request, "Access Denied: Clinical staff role required.")
        return redirect('home')

class ManagementRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'management'
    def handle_no_permission(self):
        messages.error(self.request, "Access Denied: Management role required.")
        return redirect('home')


# Dashboards
class PatientDashboardView(LoginRequiredMixin, PatientRequiredMixin, TemplateView):
    template_name = 'dashboards/patient.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.request.user.patient_profile
        context['profile'] = profile
        context['intake_form'] = PatientIntakeForm(instance=profile)
        context['predictions'] = PredictionRecord.objects.filter(patient=profile).order_by('-created_at')
        return context

    def post(self, request, *args, **kwargs):
        profile = request.user.patient_profile
        form = PatientIntakeForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            # Log intake profile update
            AuditLog.objects.create(
                user=request.user,
                action="intake_profile_updated",
                metadata={"patient_profile_id": profile.id}
            )
            messages.success(request, "Baseline clinical profile updated successfully.")
        else:
            messages.error(request, "Failed to update profile. Please verify features form.")
        return redirect('patient_dashboard')


class ServiceDashboardView(LoginRequiredMixin, DoctorNurseRequiredMixin, ListView):
    template_name = 'dashboards/service.html'
    context_object_name = 'cases'

    def get_queryset(self):
        # Allow filtering by review status
        is_reviewed = self.request.GET.get('is_reviewed')
        query = PredictionRecord.objects.all().select_related('patient__user', 'reviewed_by').order_by('-created_at')
        
        if is_reviewed == '1':
            query = query.filter(is_reviewed=True)
        elif is_reviewed == '0':
            query = query.filter(is_reviewed=False)
            
        # Search by patient name
        search = self.request.GET.get('search')
        if search:
            query = query.filter(patient__user__username__icontains=search) | \
                    query.filter(patient__user__first_name__icontains=search) | \
                    query.filter(patient__user__last_name__icontains=search)
                    
        return query

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['review_form'] = CaseReviewForm()
        # HTMX partial rendering support
        if self.request.headers.get('HX-Request') == 'true':
            self.template_name = 'dashboards/partials/case_list.html'
        return context


class ManagementDashboardView(LoginRequiredMixin, ManagementRequiredMixin, TemplateView):
    template_name = 'dashboards/management.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Fetch initial historical records for list render; JS charts will load asynchronously
        context['predictions'] = PredictionRecord.objects.all().order_by('-created_at')[:10]
        context['logs'] = AuditLog.objects.all().order_by('-timestamp')[:15]
        return context


# Public Info Views
class AboutView(TemplateView):
    template_name = 'about.html'


class ContactView(CreateView):
    model = ContactMessage
    form_class = ContactForm
    template_name = 'contact.html'
    success_url = reverse_lazy('contact')

    def form_valid(self, form):
        response = super().form_valid(form)
        message = self.object
        
        # Enqueue background Celery processing
        if message.is_critical:
            process_contact_message.apply_async(args=[message.id], queue='priority')
            messages.warning(self.request, "Critical Message Received. The on-duty team is being alerted immediately.")
        else:
            process_contact_message.delay(message.id)
            messages.success(self.request, "Message received. Our team will contact you shortly.")
            
        return response


class VRTaskView(LoginRequiredMixin, PatientRequiredMixin, TemplateView):
    template_name = "dashboards/vr_task.html"

    def post(self, request, *args, **kwargs):
        from patients.models import VRTestRecord
        from django.http import JsonResponse
        import json

        try:
            body = json.loads(request.body)
            time_taken = float(body.get("time_taken", 0))
            errors = int(body.get("errors", 0))
            score = float(body.get("score", 100))

            profile = request.user.patient_profile
            
            # Save VR test record
            vr_record = VRTestRecord.objects.create(
                patient=profile,
                time_taken=time_taken,
                errors=errors,
                score=score
            )

            # Map the 100-point game score to standard 30-point MMSE cognitive scale
            mapped_mmse = round((score / 100.0) * 30.0, 1)
            
            # Auto-update patient profile cognitive score
            profile.cognitive_score = mapped_mmse
            profile.save()

            # Audit log
            AuditLog.objects.create(
                user=request.user,
                action="vr_test_completed",
                metadata={
                    "record_id": vr_record.id,
                    "score": score,
                    "mapped_mmse": mapped_mmse
                }
            )

            messages.success(request, f"Cognitive test complete! Mapped MMSE Score: {mapped_mmse} has been updated on your profile.")

            return JsonResponse({
                "status": "SUCCESS",
                "cognitive_score": mapped_mmse,
                "redirect_url": reverse('patient_dashboard')
            })
        except Exception as e:
            return JsonResponse({
                "status": "ERROR",
                "message": str(e)
            }, status=400)

