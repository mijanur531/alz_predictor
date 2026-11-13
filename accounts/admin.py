from django.contrib import admin  # type: ignore[reportMissingModuleSource]
from django.contrib.auth.admin import UserAdmin  # type: ignore[reportMissingModuleSource]

from .models import PatientProfile, ServiceProviderProfile, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("username", "email", "first_name", "last_name")


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "age", "gender", "cognitive_score", "bmi")
    search_fields = ("user__username", "user__email")
    list_filter = ("gender", "education_level", "smoking", "family_history")


@admin.register(ServiceProviderProfile)
class ServiceProviderProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "department", "qualification")
    search_fields = ("user__username", "user__email", "department", "qualification")
    list_filter = ("department",)
