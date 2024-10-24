import csv
from django.core.management.base import BaseCommand
from dgp_bus.models import Hospital  # Update 'myapp' with your app name

class Command(BaseCommand):
    help = 'Import Hospital data from CSV'

    def handle(self, *args, **kwargs):
        # Define the CSV file path (you'll need to move the CSV to the production server)
        file_path = 'hospitals_export.csv'

        # Open the CSV file for reading
        with open(file_path, mode='r') as file:
            reader = csv.reader(file)
            next(reader)  # Skip the header row

            for row in reader:
                hospital_name, address, image_path = row

                # Create or update the hospital in the database
                Hospital.objects.update_or_create(
                    hospital_name=hospital_name,
                    defaults={'address': address, 'image_path': image_path},
                )

        self.stdout.write(self.style.SUCCESS('Data imported successfully'))
