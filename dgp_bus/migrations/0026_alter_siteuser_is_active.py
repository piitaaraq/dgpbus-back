# Generated by Django 5.1 on 2024-11-29 12:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dgp_bus', '0025_siteuser_alter_staffadminuser_role'),
    ]

    operations = [
        migrations.AlterField(
            model_name='siteuser',
            name='is_active',
            field=models.BooleanField(default=False),
        ),
    ]
