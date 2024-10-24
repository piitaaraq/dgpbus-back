from datetime import timedelta
from django.utils import timezone
from celery import shared_task
from .models import Patient

@shared_task
def delete_expired_entries():
    threshold_date = timezone.now() - timedelta(days=30)
    Patient.objects.filter(created_at__lt=threshold_date).delete()  # Deletes the entire row
