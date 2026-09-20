from rest_framework import permissions

class IsPatient(permissions.BasePermission):
    """
    Allows access only to users with the 'patient' role.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'patient'


class IsDoctorOrNurse(permissions.BasePermission):
    """
    Allows access only to doctors and nurses.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ('doctor', 'nurse')


class IsManagement(permissions.BasePermission):
    """
    Allows access only to users with the 'management' role.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'management'


class IsStaffUser(permissions.BasePermission):
    """
    Allows access to clinical and managerial staff (doctor, nurse, technician, management).
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ('doctor', 'nurse', 'technician', 'management')

