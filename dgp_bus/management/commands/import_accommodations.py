import csv
from django.core.management.base import BaseCommand
from dgp_bus.models import Accommodation  # Update this import with your app name

class Command(BaseCommand):
    help = 'Import Accommodation data from CSV'

    def handle(self, *args, **kwargs):
        file_path = 'accommodations_export.csv'

        with open(file_path, mode='r') as file:
            reader = csv.reader(file)
            next(reader)  # Skip the header row

            for row in reader:
                name = row[0]

                # Create or update the accommodation entry
                Accommodation.objects.update_or_create(
                    name=name
                )

        self.stdout.write(self.style.SUCCESS('Accommodation data imported successfully'))
