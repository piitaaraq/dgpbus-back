from django.core import signing
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import timezone
from django.utils.http import int_to_base36, base36_to_int


# Custom token generator for SiteUser
class SiteUserPasswordResetTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        """
        This is Django's default hash generation.
        """
        return f"{user.pk}{user.is_active}{timestamp}"

    def check_token(self, user, token):
        """
        Extend Django's token check to enforce PASSWORD_RESET_TIMEOUT.
        """
        if not (user and token):
            return False

        # Perform default Django validation first
        result = super().check_token(user, token)
        if not result:
            return False

        # Extract timestamp from token
        try:
            ts_b36, _ = token.split("-")
            ts = base36_to_int(ts_b36)
        except Exception:
            return False

        # Calculate time delta, making sure we're using naive UTC datetime
        naive_now = timezone.now().replace(tzinfo=None)
        now_ts = self._num_seconds(naive_now)

        timeout = getattr(settings, 'PASSWORD_RESET_TIMEOUT', 60 * 60 * 3)

        if (now_ts - ts) > timeout:
            return False

        return True


# Create instance for re-use
site_user_password_reset_token = SiteUserPasswordResetTokenGenerator()


# Generate signed data for email link
def generate_signed_reset_data(user):
    token = site_user_password_reset_token.make_token(user)
    data = {'email': user.email, 'token': token}
    signed_data = signing.dumps(data)
    return signed_data


# Verify signed data when link is opened
def verify_signed_reset_data(signed_data):
    try:
        data = signing.loads(signed_data)
        return data['email'], data['token']
    except signing.BadSignature:
        return None, None


# Send password reset email using Mailgun via Django's EmailBackend
def send_password_reset_email(user):
    signed_data = generate_signed_reset_data(user)
    reset_link = f"{settings.FRONTEND_RESET_URL}?signed={signed_data}"
    subject = "Anmodning om nulstilling af adgangskode"
    message = f"""
    Hej,

    Vi har modtaget en anmodning om nulstilling af din adgangskode til bus.patienthjem.dk.

    Klik på linket nedenunder, eller kopier adressen til din browser, for at nulstille din adgangskode:

    {reset_link}

    For din egen sikkerhed vil linket udløbe om tre timer.

    Hvis du ikke selv har anmodet om en nulstilling af adgangskoden, kan du blot se bort fra denne e-mail.

    Venlig hilsen,
    bus.patienthjem.dk teamet
    """

    send_mail(
        subject=subject,
        message=message.strip(),
        from_email="noreply@bus.patienthjem.dk",
        recipient_list=[user.email],
    )


# For testing imports in Django shell (optional)
def test_import():
    print("UTILS IMPORT WORKS")
