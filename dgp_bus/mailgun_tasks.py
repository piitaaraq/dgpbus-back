from django.core.mail import send_mail
from django.conf import settings
from celery import shared_task

@shared_task
def send_smtp_email(subject, message, to_email_list):
    print("[DEBUG] Email host:", settings.EMAIL_HOST)
    print("[DEBUG] Port:", settings.EMAIL_PORT)
    print("[DEBUG] Username:", settings.EMAIL_HOST_USER)

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=None,  # uses DEFAULT_FROM_EMAIL
            recipient_list=to_email_list,
            fail_silently=False,
        )
        print(f"[INFO] Sent email to {to_email_list}")
    except Exception as e:
        print(f"[ERROR] Failed to send email to {to_email_list}: {e}")
