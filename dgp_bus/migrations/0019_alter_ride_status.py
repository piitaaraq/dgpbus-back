# Generated by Django 5.1 on 2024-10-02 11:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dgp_bus', '0018_patient_has_taxi'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ride',
            name='status',
            field=models.BooleanField(default=False),
        ),
    ]
