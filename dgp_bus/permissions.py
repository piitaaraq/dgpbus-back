# dgp_bus/permissions.py
from rest_framework.permissions import BasePermission
from django.contrib.auth import get_user_model
from dgp_bus.models import SiteUser

class IsSiteUser(BasePermission):
    """
    Site-level access: allow any authenticated account when SiteUser is the AUTH_USER_MODEL.
    Keeps the hook for future role rules.
    """
    message = "Login required for site pages."

    def has_permission(self, request, view):
        u = request.user
        if not (u and u.is_authenticated and getattr(u, "is_active", True)):
            return False

        # If SiteUser is your concrete user model, we're done.
        if get_user_model() is SiteUser:
            return True

        # (Fallback if SiteUser were a profile model; not your case)
        return hasattr(u, "siteuser")
