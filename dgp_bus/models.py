from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.auth.hashers import make_password


class StaffAdminManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)  # Hash the password
        else:
            user.set_unusable_password()  # Ensure no password is set if not provided
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_admin', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_admin') is not True:
            raise ValueError('Superuser must have is_admin=True.')

        return self.create_user(email, password, **extra_fields)

class StaffAdminUser(AbstractBaseUser):
    ROLE_CHOICES = [
        ('staff', 'Staff'),
        ('admin', 'Admin'),
    ]

    email = models.CharField(max_length=150, unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    # Timestamp fields
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = StaffAdminManager()

    def save(self, *args, **kwargs):
        # Avoid hashing the password multiple times if it's already hashed
        if self.pk and self.password and not self.password.startswith('pbkdf2_sha256$'):
            self.set_password(self.password)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email


class Hospital(models.Model):
    hospital_name = models.CharField(max_length=255)
    address = models.TextField()
    image_path = models.CharField(max_length=255)

    def __str__(self):
        return self.hospital_name

class Fake_Hospital(models.Model):
    hospital_name = models.CharField(max_length=255)
    address = models.TextField()
    image_path = models.CharField(max_length=255)

    def __str__(self):
        return self.hospital_name

class Schedule(models.Model):
    destination = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    day_of_week = models.CharField(max_length=20)
    departure_time = models.TimeField()
    departure_location = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.departure_location} to {self.destination.hospital_name} on {self.day_of_week}'

class Accommodation(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Patient(models.Model):
    name = models.CharField(max_length=255)
    room = models.CharField(max_length=100)
    appointment_time = models.TimeField()
    appointment_date = models.DateField()
    bus_time = models.TimeField(null=True, blank=True)  # Optional field
    translator = models.BooleanField(default=False)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    department = models.CharField(max_length=255, null=True, blank=True)
    description = models.CharField(max_length=255, blank=True)
    phone_no = models.CharField(max_length=15, blank=True, null=True)
    has_taxi = models.BooleanField(default=False)
    accommodation = models.ForeignKey(Accommodation, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name} - Room {self.room} - {self.hospital.hospital_name}'


class Ride(models.Model):
    date = models.DateField(default=timezone.now)
    departure_time = models.TimeField()
    arrival_time = models.TimeField(null=True, blank=True)
    departure_location = models.CharField(max_length=255)
    destination = models.ForeignKey('Hospital', on_delete=models.CASCADE)
    users = models.ManyToManyField('Patient', related_name='rides')
    status = models.BooleanField(default=False)

    def __str__(self):
        return f"Ride to {self.destination} on {self.date} at {self.departure_time}"
