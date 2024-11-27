from rest_framework.permissions import BasePermission
from dgp_bus.models import SiteUser


class IsSiteUser(BasePermission):
    """
    Custom permission to allow access only to SiteUser accounts.
    """

    def has_permission(self, request, view):
        # Ensure the user is authenticated and is a SiteUser
        return request.user.is_authenticated and isinstance(request.user, SiteUser)
