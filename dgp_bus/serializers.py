from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Hospital, Schedule, Patient, Ride, StaffAdminUser, Accommodation, RidePatient, SiteUser
from datetime import datetime, timedelta
import locale
import bleach

class HospitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = '__all__'

class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = '__all__'

class AccommodationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Accommodation
        fields = ['id', 'name']


class StaffAdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffAdminUser
        fields = ['id', 'email', 'role', 'is_active', 'is_staff', 'is_admin', 'password', 'date_joined', 'last_login']
        extra_kwargs = {
            'password': {'write_only': True}  # Ensure password is write-only
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = StaffAdminUser(**validated_data)
        if password:
            user.set_password(password)  # Hash the password
        else:
            user.set_unusable_password()  # Ensure no password is set if not provided
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)  # Hash the password if provided

        instance.save()
        return instance

# Create users / staff or admin
class RegisterUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = StaffAdminUser
        fields = ['email', 'password', 'role']

    def create(self, validated_data):
        user = StaffAdminUser(
            email=validated_data['email'],
            role=validated_data['role'],
        )
        user.set_password(validated_data['password'])  # Hash the password
        user.is_active = False  # User requires admin approval
        user.save()
        return user

class ApproveUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffAdminUser
        fields = ['id', 'email', 'role', 'is_active']  # Include additional fields like email, role

    def update(self, instance, validated_data):
        instance.is_active = validated_data.get('is_active', instance.is_active)
        instance.save()
        return instance

class SiteUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteUser
        fields = ['email', 'password']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def create(self, validated_data):
        user = SiteUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password']
        )
        # Set is_active to False for admin approval
        user.is_active = False
        user.save()
        return user




class PatientSerializer(serializers.ModelSerializer):
    needs_translator = serializers.BooleanField(write_only=True)
    translator = serializers.BooleanField(read_only=True)
    description = serializers.CharField(required=False, allow_blank=True, max_length=255)
    hospital_name = serializers.CharField(source='hospital.hospital_name', read_only=True)
    has_taxi = serializers.BooleanField(default=False)

    # Use the AccommodationSerializer to serialize the accommodation foreign key
    accommodation = AccommodationSerializer(read_only=True)
    accommodation_id = serializers.PrimaryKeyRelatedField(
        queryset=Accommodation.objects.all(), source='accommodation', write_only=True
    )

    class Meta:
        model = Patient
        fields = '__all__'
        extra_fields = ['hospital_name', 'accommodation', 'accommodation_id']

    # Sanitize the description field to prevent XSS attacks
    def sanitize_description(self, description):
        return bleach.clean(description, tags=[], attributes={}, strip=True)

    def calculate_bus_time(self, patient):
        # Set locale to Danish
        locale.setlocale(locale.LC_TIME, 'da_DK.UTF-8')
        
        accommodation = patient.get('accommodation')
        hospital = patient.get('hospital')
        
        print(f"Accommodation: {accommodation.name}, Hospital ID: {hospital.id}")
        
        # Only calculate bus_time for hospitals with IDs 1, 3, and 7
        if hospital.id in [1, 3, 7] and accommodation.name == 'Det grønlandske Patienthjem':
            appointment_date = patient.get('appointment_date')
            appointment_time = patient.get('appointment_time')
            
            # Get the day of the week
            day_of_week = appointment_date.strftime('%A')
    
            # Use the schedule for hospital 1 for hospitals 3 and 7
            schedule_hospital_id = 1 if hospital.id in [3, 7] else hospital.id
    
            # Fetch schedules using the adjusted hospital ID
            schedules = Schedule.objects.filter(destination_id=schedule_hospital_id, day_of_week=day_of_week)
            
            suitable_schedule = None
            for schedule in schedules:
                travel_time = timedelta(minutes=30)
                latest_departure = (datetime.combine(appointment_date, appointment_time) - travel_time).time()
                
                # Find the latest schedule before the latest_departure time
                if schedule.departure_time <= latest_departure:
                    if suitable_schedule is None or schedule.departure_time > suitable_schedule.departure_time:
                        suitable_schedule = schedule
            
            # Return the departure_time of the suitable schedule
            return suitable_schedule.departure_time if suitable_schedule else None
        else:
            return None

    def create(self, validated_data):
        if 'description' in validated_data:
            validated_data['description'] = self.sanitize_description(validated_data['description'])

        needs_translator = validated_data.pop('needs_translator', False)
        validated_data['bus_time'] = self.calculate_bus_time(validated_data)
        patient = super().create(validated_data)

        patient.translator = needs_translator
        patient.save()

        self.assign_patient_to_ride(patient)
        return patient

    def update(self, instance, validated_data):
        if 'description' in validated_data:
            validated_data['description'] = self.sanitize_description(validated_data['description'])

        validated_data['bus_time'] = self.calculate_bus_time(validated_data)
        patient = super().update(instance, validated_data)

        self.assign_patient_to_ride(patient)
        return patient

    def assign_patient_to_ride(self, patient):
        if not patient.bus_time:
            return
    
        # Find or create a Ride based on the patient's appointment details
        ride, created = Ride.objects.get_or_create(
            date=patient.appointment_date,
            departure_time=patient.bus_time,
            destination=patient.hospital,
            defaults={'departure_location': 'Default Location'}
        )
    
        # Check if the patient is already assigned to this ride
        if not RidePatient.objects.filter(ride=ride, patient=patient).exists():
            # Use the RidePatient model to assign the patient to the ride
            RidePatient.objects.create(ride=ride, patient=patient)
    

class PatientPublicSerializer(serializers.ModelSerializer):
    hospital_name = serializers.CharField(source='hospital.hospital_name', read_only=True)

    class Meta:
        model = Patient
        exclude = ['description']  # Exclude the description field
        extra_fields = ['hospital_name']


class RideSerializer(serializers.ModelSerializer):
    hospital_name = serializers.CharField(source='destination.hospital_name', read_only=True)
    patients = serializers.SerializerMethodField()

    class Meta:
        model = Ride
        fields = ['id', 'date', 'departure_time', 'departure_location', 'hospital_name', 'patients']

    def get_patients(self, obj):
        # Fetch related patients using the RidePatient model
        ride_patients = RidePatient.objects.filter(ride=obj)
        return RidePatientSerializer(ride_patients, many=True).data

class RidePatientSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    patient_room = serializers.CharField(source='patient.room', read_only=True)

    class Meta:
        model = RidePatient
        fields = ['patient_name', 'patient_room', 'checked_in']

# for fetching data without cpr. nr.
class RidePublicSerializer(serializers.ModelSerializer):
    patients = PatientPublicSerializer(many=True, source='users')  # Use the public version of PatientSerializer

    class Meta:
        model = Ride
        fields = '__all__'  # Include all fields except the excluded ones in PatientPublicSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # Replace 'username' with 'email' in the authentication process
        attrs['username'] = attrs.get('email', '')
        return super().validate(attrs)
