# Generated by Django 5.1 on 2025-04-15 12:17

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dgp_bus', '0003_remove_ridepatient_ride_remove_ridepatient_patient_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='patient',
            name='day_of_birth',
            field=models.DateField(default=datetime.datetime(2025, 4, 15, 12, 17, 9, 10649, tzinfo=datetime.timezone.utc)),
            preserve_default=False,
        ),
    ]
