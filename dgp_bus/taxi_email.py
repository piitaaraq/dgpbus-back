# taxi_email.py
import requests
from django.conf import settings
from celery import shared_task
from .models import SiteUser
from .tasks import send_smtp_email

@shared_task
def send_taxi_user_report():

    try:
        response = requests.get(f"{settings.BASE_URL}/api/patients/taxi-users")
        response.raise_for_status()
        patients = response.json()
    except requests.RequestException as e:
        print(f"[ERROR] Failed to fetch patient data: {e}")
        return

    patients_without_taxi = [p for p in patients if not p.get("has_taxi", False)]
    print(f"[DEBUG] Patients without taxi: {len(patients_without_taxi)}")

    if not patients_without_taxi:
        print("[INFO] No patients without taxi to report.")
        return

    # Compose message
    message = "Patienter uden taxa\n\n"
    for patient in patients_without_taxi:
        name = patient.get('name', 'Ukendt')
        accommodation = patient.get('accommodation', {}).get("name", "N/A")
        hospital = patient.get('hospital_name', 'UkendtHospital')
        appointment = patient.get('appointment_time', 'Ingen aftale')

        if appointment != 'Ingen aftale':
            appointment = appointment[:5]  # Trim to HH:MM

        message += (
            f"- {name}\n"
            f"  Indkvartering: {accommodation}\n"
            f"  Hospital: {hospital}\n"
            f"  Tid på hospitalet: {appointment}\n\n"
        )

    # Get the list of front desk users
    recipient_list = list(SiteUser.objects.filter(is_frontdesk=True).values_list('email', flat=True))

    if recipient_list:

        send_smtp_email.delay(
            "Dagens liste med patienter der mangler en taxa",
            message,
            recipient_list
        )
    else:
        print("[INFO] No frontdesk users marked to receive report.")