from django.core import signing
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import timezone
from django.utils.http import int_to_base36, base36_to_int
from urllib.parse import urlencode

# ------------------------
# Password Reset Tokens
# ------------------------

class SiteUserPasswordResetTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return f"{user.pk}{user.is_active}{timestamp}"

    def check_token(self, user, token):
        if not (user and token):
            return False

        result = super().check_token(user, token)
        if not result:
            return False

        try:
            ts_b36, _ = token.split("-")
            ts = base36_to_int(ts_b36)
        except Exception:
            return False

        naive_now = timezone.now().replace(tzinfo=None)
        now_ts = self._num_seconds(naive_now)

        timeout = getattr(settings, 'PASSWORD_RESET_TIMEOUT', 60 * 60 * 3)

        if (now_ts - ts) > timeout:
            return False

        return True

site_user_password_reset_token = SiteUserPasswordResetTokenGenerator()


def generate_signed_reset_data(user):
    token = site_user_password_reset_token.make_token(user)
    data = {'email': user.email, 'token': token}
    signed_data = signing.dumps(data)
    return signed_data



def verify_signed_reset_data(signed_data):
    try:
        data = signing.loads(signed_data)
        return data['email'], data['token']
    except signing.BadSignature:
        return None, None


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

# ------------------------
# Invite Tokens
# ------------------------

INVITE_TOKEN_SALT = "siteuser.invite.token"

def generate_signed_invite_data(email):
    signer = signing.TimestampSigner(salt=INVITE_TOKEN_SALT)
    signed_value = signer.sign(email)
    return signed_value

def verify_signed_invite_data(signed_data):
    signer = signing.TimestampSigner(salt=INVITE_TOKEN_SALT)
    print(f"[DEBUG] Verifying invite token: '{signed_data}'")
    print(f"[DEBUG] Using salt: '{INVITE_TOKEN_SALT}'")
    print(f"[DEBUG] Using INVITE_TOKEN_EXPIRY: '{settings.INVITE_TOKEN_EXPIRY}'")
    try:
        email = signer.unsign(signed_data, max_age=settings.INVITE_TOKEN_EXPIRY)
        print(f"[DEBUG] Invite token valid for email: '{email}'")
        return email
    except signing.SignatureExpired:
        print("[DEBUG] Invite token expired")
        return None
    except signing.BadSignature as e:
        print(f"[DEBUG] BadSignature: '{str(e)}'")
        return None

#def verify_signed_invite_data(signed_data):
#    signer = signing.TimestampSigner(salt=INVITE_TOKEN_SALT)
#    try:
#        email = signer.unsign(signed_data, max_age=settings.INVITE_TOKEN_EXPIRY)
#        return email
#    except signing.SignatureExpired:
#        return None
#    except signing.BadSignature:
#        return None

def send_invite_email(email):
    signed_data = generate_signed_invite_data(email)
    invite_link = f"{settings.FRONTEND_INVITE_URL}?{urlencode({'signed': signed_data})}"
    subject = "Invitation til at oprette konto på bus.patienthjem.dk"
    message = f"""
    Hej,

    Du er inviteret til at oprette en konto på bus.patienthjem.dk.

    Klik på linket nedenunder, eller kopier adressen til din browser, for at oprette din adgangskode:

    {invite_link}

    For din egen sikkerhed udløber dette link efter {settings.INVITE_TOKEN_EXPIRY // 3600} timer.

    Venlig hilsen,
    bus.patienthjem.dk teamet
    """

    send_mail(
        subject=subject,
        message=message.strip(),
        from_email="noreply@bus.patienthjem.dk",
        recipient_list=[email],
    )