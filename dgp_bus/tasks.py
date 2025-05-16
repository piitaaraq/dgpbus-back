from datetime import timedelta
from django.utils import timezone
from celery import shared_task
from .models import Patient
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def delete_expired_entries():
    threshold_date = timezone.now() - timedelta(days=30)
    Patient.objects.filter(created_at__lt=threshold_date).delete()  # Deletes the entire row


@shared_task
def send_smtp_email(subject, message, to_email_list):

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email="taxapatienter@mail.patienthjem.dk",  # uses DEFAULT_FROM_EMAIL
            recipient_list=to_email_list,
            fail_silently=False,
        )
        print(f"[INFO] Sent email to {to_email_list}")
    except Exception as e:
        print(f"[ERROR] Failed to send email to {to_email_list}: {e}")