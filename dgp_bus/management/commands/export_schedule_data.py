import csv
from django.core.management.base import BaseCommand
from dgp_bus.models import Schedule  # Update this import with your app name

class Command(BaseCommand):
    help = 'Export Schedule data to CSV'

    def handle(self, *args, **kwargs):
        file_path = 'schedules_export.csv'

        with open(file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Destination ID', 'Day of Week', 'Departure Time', 'Departure Location'])

            schedules = Schedule.objects.all()

            for schedule in schedules:
                writer.writerow([
                    schedule.destination_id,  # Export the ForeignKey as the destination's ID
                    schedule.day_of_week,
                    schedule.departure_time,
                    schedule.departure_location
                ])

        self.stdout.write(self.style.SUCCESS(f'Schedule data exported to {file_path}'))
