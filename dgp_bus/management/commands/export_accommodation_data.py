import csv
from django.core.management.base import BaseCommand
from dgp_bus.models import Accommodation  # Update this import with your app name

class Command(BaseCommand):
    help = 'Export Accommodation data to CSV'

    def handle(self, *args, **kwargs):
        file_path = 'accommodations_export.csv'

        with open(file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Name'])

            accommodations = Accommodation.objects.all()

            for accommodation in accommodations:
                writer.writerow([accommodation.name])

        self.stdout.write(self.style.SUCCESS(f'Accommodation data exported to {file_path}'))
