# Generated by Django 5.1 on 2025-01-02 10:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dgp_bus', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hospital',
            name='image_path',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]