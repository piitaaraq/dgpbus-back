import csv
from django.core.management.base import BaseCommand
from dgp_bus.models import Hospital 

class Command(BaseCommand):
    help = 'Export Hospital data to CSV'

    def handle(self, *args, **kwargs):
        # Define the CSV file path
        file_path = 'hospitals_export.csv'

        # Open a CSV file for writing
        with open(file_path, mode='w', newline='') as file:
            writer = csv.writer(file)

            # Write the header
            writer.writerow(['Hospital Name', 'Address', 'Image Path'])

            # Fetch all hospital records
            hospitals = Hospital.objects.all()

            # Write hospital data
            for hospital in hospitals:
                writer.writerow([hospital.hospital_name, hospital.address, hospital.image_path])

        self.stdout.write(self.style.SUCCESS(f'Data exported to {file_path}'))
