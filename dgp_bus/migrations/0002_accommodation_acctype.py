# Generated by Django 5.1.4 on 2024-12-30 12:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dgp_bus', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='accommodation',
            name='accType',
            field=models.CharField(default='hotel', max_length=255),
            preserve_default=False,
        ),
    ]
