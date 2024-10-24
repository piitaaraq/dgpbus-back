import csv
from django.core.management.base import BaseCommand
from dgp_bus.models import Schedule, Hospital  # Update this import with your app name

class Command(BaseCommand):
    help = 'Import Schedule data from CSV'

    def handle(self, *args, **kwargs):
        file_path = 'schedules_export.csv'

        with open(file_path, mode='r') as file:
            reader = csv.reader(file)
            next(reader)  # Skip the header row

            for row in reader:
                destination_id, day_of_week, departure_time, departure_location = row

                # Fetch the hospital by its ID (ensure hospitals are already in the database)
                try:
                    hospital = Hospital.objects.get(id=destination_id)
                except Hospital.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f'Hospital with ID {destination_id} not found'))
                    continue

                # Create or update the schedule
                Schedule.objects.update_or_create(
                    destination=hospital,
                    day_of_week=day_of_week,
                    defaults={
                        'departure_time': departure_time,
                        'departure_location': departure_location
                    }
                )

        self.stdout.write(self.style.SUCCESS('Schedule data imported successfully'))
