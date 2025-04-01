# Generated by Django 5.1 on 2025-02-18 11:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dgp_bus', '0002_alter_hospital_image_path'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ridepatient',
            name='ride',
        ),
        migrations.RemoveField(
            model_name='ridepatient',
            name='patient',
        ),
        migrations.AddField(
            model_name='patient',
            name='departure_location',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='patient',
            name='status',
            field=models.BooleanField(default=False),
        ),
        migrations.DeleteModel(
            name='Ride',
        ),
        migrations.DeleteModel(
            name='RidePatient',
        ),
    ]
