# Generated by Django 5.1 on 2024-12-30 21:16

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Accommodation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('accType', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Hospital',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hospital_name', models.CharField(max_length=255)),
                ('address', models.TextField()),
                ('image_path', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='SiteUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('email', models.EmailField(max_length=150, unique=True)),
                ('is_active', models.BooleanField(default=False)),
                ('date_joined', models.DateTimeField(auto_now_add=True)),
                ('last_login', models.DateTimeField(auto_now=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StaffAdminUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('email', models.EmailField(max_length=150, unique=True)),
                ('role', models.CharField(choices=[('staff', 'Staff'), ('admin', 'Admin')], default='staff', max_length=10)),
                ('is_active', models.BooleanField(default=True)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_admin', models.BooleanField(default=False)),
                ('date_joined', models.DateTimeField(auto_now_add=True)),
                ('last_login', models.DateTimeField(auto_now=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Patient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('room', models.CharField(max_length=100)),
                ('appointment_time', models.TimeField()),
                ('appointment_date', models.DateField()),
                ('bus_time', models.TimeField(blank=True, null=True)),
                ('translator', models.BooleanField(default=False)),
                ('department', models.CharField(blank=True, max_length=255, null=True)),
                ('description', models.CharField(blank=True, max_length=255)),
                ('phone_no', models.CharField(blank=True, max_length=15, null=True)),
                ('has_taxi', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('wheelchair', models.BooleanField(default=False)),
                ('trolley', models.BooleanField(default=False)),
                ('companion', models.BooleanField(default=False)),
                ('accommodation', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='dgp_bus.accommodation')),
                ('hospital', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dgp_bus.hospital')),
            ],
        ),
        migrations.CreateModel(
            name='Ride',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=django.utils.timezone.now)),
                ('departure_time', models.TimeField()),
                ('departure_location', models.CharField(max_length=255)),
                ('status', models.BooleanField(default=False)),
                ('max_capacity', models.PositiveIntegerField(default=10)),
                ('destination', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dgp_bus.hospital')),
            ],
        ),
        migrations.CreateModel(
            name='RidePatient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('checked_in', models.BooleanField(default=False)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dgp_bus.patient')),
                ('ride', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dgp_bus.ride')),
            ],
        ),
        migrations.AddField(
            model_name='ride',
            name='patients',
            field=models.ManyToManyField(related_name='rides', through='dgp_bus.RidePatient', to='dgp_bus.patient'),
        ),
        migrations.CreateModel(
            name='Schedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day_of_week', models.CharField(max_length=20)),
                ('departure_time', models.TimeField()),
                ('departure_location', models.CharField(max_length=255)),
                ('destination', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dgp_bus.hospital')),
            ],
        ),
    ]
