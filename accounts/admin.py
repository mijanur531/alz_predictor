from django.contrib import admin  # type: ignore[reportMissingModuleSource]
from django.contrib.auth.admin import UserAdmin  # type: ignore[reportMissingModuleSource]

from .models import PatientProfile, ServiceProviderProfile, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    pass


@admin.register(PatientProfile, ServiceProviderProfile)
class ProfileAdmin(admin.ModelAdmin):
    pass
