from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'

class IsStaff(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'staff'

class IsPatient(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'patient'

class IsStaffOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['staff', 'admin']

