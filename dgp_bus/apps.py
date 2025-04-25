from django.apps import AppConfig

class DgpBusConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dgp_bus'

    def ready(self):
        # Import your Celery task module here so it's registered after the app registry is ready
        from . import taxi_email
