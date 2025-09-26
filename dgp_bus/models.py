from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin



class StaffAdminManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_admin') is not True:
            raise ValueError('Superuser must have is_admin=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class StaffAdminUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('staff', 'Staff'),
        ('admin', 'Admin'),
    ]

    email = models.EmailField(max_length=150, unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='staff')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    # Timestamps
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = StaffAdminManager()

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

# site user
class SiteUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

class SiteUser(AbstractBaseUser):
    email = models.EmailField(max_length=150, unique=True)
    is_frontdesk = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)  # Default to False
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = SiteUserManager()

    def __str__(self):
        return self.email


# Hospital model
class Hospital(models.Model):
    hospital_name = models.CharField(max_length=255)
    address = models.TextField()
    image_path = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.hospital_name




# Schedule model
class Schedule(models.Model):
    destination = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    day_of_week = models.CharField(max_length=20)
    departure_time = models.TimeField()
    departure_location = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.departure_location} to {self.destination.hospital_name} on {self.day_of_week}'


# Accommodation model
class Accommodation(models.Model):
    name = models.CharField(max_length=255) # force
    accType = models.CharField(max_length=255)


    def __str__(self):
        return self.name

class Patient(models.Model):
    # personal-only
    name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    day_of_birth = models.DateField(null=True, blank=True)
    phone_no = models.CharField(max_length=15, blank=True, null=True)
    room = models.CharField(max_length=100, blank=True, null=True)  # keep here if room is person-scoped
    # optional: default accommodation used when appointment.accommodation is null
    default_accommodation = models.ForeignKey(
        'Accommodation', on_delete=models.SET_NULL, null=True, blank=True, related_name='default_for_patients'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['name', 'last_name'])]

    def __str__(self):
        return f'{self.name} {self.last_name}'.strip()


class Appointment(models.Model):
    patient = models.ForeignKey('Patient', on_delete=models.CASCADE, related_name='appointments')
    hospital = models.ForeignKey('Hospital', on_delete=models.PROTECT)
    accommodation = models.ForeignKey('Accommodation', on_delete=models.PROTECT, null=True, blank=True)

    appointment_date = models.DateField()
    appointment_time = models.TimeField()

    # bus time (manual override vs computed)
    bus_time_manual = models.TimeField(null=True, blank=True)
    bus_time_computed = models.TimeField(null=True, blank=True)

    # appointment-scoped flags
    status = models.BooleanField(default=False)
    translator = models.BooleanField(default=False)
    has_taxi = models.BooleanField(default=False)
    wheelchair = models.BooleanField(default=False)
    trolley = models.BooleanField(default=False)
    companion = models.BooleanField(default=False)

    department = models.CharField(max_length=255, null=True, blank=True)
    description = models.CharField(max_length=255, blank=True)
    departure_location = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['appointment_date']),
            models.Index(fields=['appointment_date', 'appointment_time']),
        ]

    @property
    def bus_time_effective(self):
        return self.bus_time_manual or self.bus_time_computed

