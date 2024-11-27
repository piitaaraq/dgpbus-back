from django.contrib.auth.backends import BaseBackend
from dgp_bus.models import SiteUser


class SiteUserBackend(BaseBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        try:
            user = SiteUser.objects.get(email=email)
            if not user.is_active:  # Check if the user is approved
                return None
            if user.check_password(password):
                return user
        except SiteUser.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return SiteUser.objects.get(pk=user_id)
        except SiteUser.DoesNotExist:
            return None
