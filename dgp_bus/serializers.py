from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Hospital, Schedule, Patient, Appointment, StaffAdminUser, Accommodation, SiteUser
from datetime import datetime, timedelta
import locale
from .utils import site_user_password_reset_token




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

class SiteUserInviteSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        # Check if user already exists
        if SiteUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Brugeren findes allerede.")
        return value

    def create(self, validated_data):
        from .utils import send_invite_email
        send_invite_email(validated_data['email'])
        return validated_data

class SiteUserInviteConfirmSerializer(serializers.Serializer):
    signed = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        from .utils import verify_signed_invite_data
        import unicodedata

        signed_data = data.get("signed")

        # Defensive normalization
        signed_data = signed_data.strip()
        signed_data = unicodedata.normalize("NFC", signed_data)

        print(f"[DEBUG] Serializer received signed data: '{signed_data}'")

        email = verify_signed_invite_data(signed_data)
        if not email:
            raise serializers.ValidationError("Ugyldigt eller udløbet link.")

        data['email'] = email
        return data

    def save(self):
        from .models import SiteUser

        email = self.validated_data['email']
        password = self.validated_data['password']

        try:
            user = SiteUser.objects.get(email=email)
        except SiteUser.DoesNotExist:
            raise serializers.ValidationError("Inviteret bruger findes ikke.")

        user.set_password(password)
        user.is_active = True
        user.save()


class SiteUserPasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not SiteUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user found with this email.")
        return value


class SiteUserPasswordResetConfirmSerializer(serializers.Serializer):
    signed = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        from .utils import verify_signed_reset_data

        signed_data = data.get("signed")
        email, token = verify_signed_reset_data(signed_data)
        if not email or not token:
            raise serializers.ValidationError("Invalid or expired reset link.")

        try:
            user = SiteUser.objects.get(email=email)
        except SiteUser.DoesNotExist:
            raise serializers.ValidationError("Invalid email.")

        if not site_user_password_reset_token.check_token(user, token):
            raise serializers.ValidationError("Invalid or expired token.")

        data['user'] = user
        return data

    def save(self):
        user = self.validated_data['user']
        user.set_password(self.validated_data['new_password'])
        user.save()


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = '__all__'


class AppointmentSerializer(serializers.ModelSerializer):
    # ---------- write via IDs ----------
    patient_id = serializers.PrimaryKeyRelatedField(
        queryset=Patient.objects.all(), source='patient', write_only=True
    )
    hospital_id = serializers.PrimaryKeyRelatedField(
        queryset=Hospital.objects.all(), source='hospital', write_only=True
    )
    accommodation_id = serializers.PrimaryKeyRelatedField(
        queryset=Accommodation.objects.all(), source='accommodation',
        write_only=True, required=False, allow_null=True
    )

    # ---------- read-only display helpers ----------
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    patient_last_name = serializers.CharField(source='patient.last_name', read_only=True)
    patient_room = serializers.CharField(source='patient.room', read_only=True)
    hospital_name = serializers.CharField(source='hospital.hospital_name', read_only=True)
    accommodation_name = serializers.SerializerMethodField(read_only=True)
    bus_time_effective = serializers.SerializerMethodField(read_only=True)
    patient_phone = serializers.CharField(source='patient.phone_no', read_only=True, allow_blank=True, allow_null=True)  
    patient_dob = serializers.DateField(source='patient.day_of_birth', read_only=True)
    patient_translator = serializers.BooleanField(source='patient.translator', read_only=True)

    class Meta:
        model = Appointment
        fields = '__all__'
        read_only_fields = ('has_taxi', 'status', 'bus_time_computed', 'created_at')
        extra_kwargs = {
            # 👇 important: prevent DRF from requiring model FKs on input
            'patient': {'read_only': True},
            'hospital': {'read_only': True},
            'accommodation': {'read_only': True},
        }

    # ---------- display helpers ----------
    def get_accommodation_name(self, obj):
        return obj.accommodation.name if obj.accommodation else None

    def get_bus_time_effective(self, obj):
        return obj.bus_time_manual or obj.bus_time_computed

    # ---------- bus-time core ----------
    @staticmethod
    def _compute_bus_time(*, hospital, accommodation, appointment_date, appointment_time):
        if not (hospital and accommodation and appointment_date and appointment_time):
            return None

        # Locale can be missing on server; don't crash if it is
        try:
            locale.setlocale(locale.LC_TIME, 'da_DK.UTF-8')
        except Exception:
            pass

        # Business rule
        if hospital.id in [1, 3, 7, 10] and getattr(accommodation, 'name', '') == 'Det grønlandske Patienthjem':
            day_of_week = appointment_date.strftime('%A')
            schedule_hospital_id = 1 if hospital.id in [3, 7, 10] else hospital.id

            schedules = Schedule.objects.filter(
                destination_id=schedule_hospital_id,
                day_of_week=day_of_week
            )

            travel_time = timedelta(minutes=30)
            latest_departure = (datetime.combine(appointment_date, appointment_time) - travel_time).time()

            chosen = None
            for s in schedules:
                if s.departure_time <= latest_departure and (chosen is None or s.departure_time > chosen.departure_time):
                    chosen = s
            return chosen.departure_time if chosen else None

        return None

    def _resolve_inputs(self, instance, v):
        """
        Resolve inputs from incoming validated data (v) or fall back to instance fields.
        """
        hospital = v.get('hospital') or getattr(instance, 'hospital', None)
        accommodation = v.get('accommodation') or getattr(instance, 'accommodation', None)
        d = v.get('appointment_date') or getattr(instance, 'appointment_date', None)
        t = v.get('appointment_time') or getattr(instance, 'appointment_time', None)
        return hospital, accommodation, d, t

    # ---------- lifecycle ----------
    def create(self, validated_data):
        # If the client didn’t set a manual bus time, compute one
        if not validated_data.get('bus_time_manual'):
            hospital, accommodation, d, t = self._resolve_inputs(None, validated_data)
            bt = self._compute_bus_time(hospital=hospital, accommodation=accommodation,
                                        appointment_date=d, appointment_time=t)
            if bt is not None:
                validated_data['bus_time_computed'] = bt
        return super().create(validated_data)

    def update(self, instance, validated_data):
        manual_provided = 'bus_time_manual' in validated_data and validated_data.get('bus_time_manual') not in (None, '')
        manual_cleared = 'bus_time_manual' in validated_data and validated_data.get('bus_time_manual') in (None, '')

        if manual_provided:
            # Respect manual override; do not touch computed here
            return super().update(instance, validated_data)

        # Either manual was cleared or inputs may have changed — recompute
        hospital, accommodation, d, t = self._resolve_inputs(instance, validated_data)
        bt = self._compute_bus_time(hospital=hospital, accommodation=accommodation,
                                    appointment_date=d, appointment_time=t)

        if manual_cleared:
            validated_data['bus_time_manual'] = None  # explicit clear back to computed

        if bt is not None:
            validated_data['bus_time_computed'] = bt

        return super().update(instance, validated_data)



class BusTimeInputSerializer(serializers.Serializer):
    hospital_id = serializers.PrimaryKeyRelatedField(
        queryset=Hospital.objects.all(), source='hospital'
    )
    accommodation_id = serializers.PrimaryKeyRelatedField(
        queryset=Accommodation.objects.all(), source='accommodation'
    )
    appointment_date = serializers.DateField()
    appointment_time = serializers.TimeField()

class AppointmentPublicSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    patient_room = serializers.CharField(source='patient.room', read_only=True)
    hospital_name = serializers.CharField(source='hospital.hospital_name', read_only=True)
    accommodation_name = serializers.SerializerMethodField(read_only=True)
    bus_time_effective = serializers.SerializerMethodField(read_only=True)

    # effective bus time as a string (client-friendly)
    bus_time_effective = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Appointment
        # expose only what you’re comfortable showing publicly
        fields = [
            'id',
            'patient_name', 'hospital_name', 'accommodation_name',
            'appointment_date', 'appointment_time', 'bus_time_effective',
            'has_taxi',  # include/remove as needed
        ]

    def get_accommodation_name(self, obj):
        return obj.accommodation.name if obj.accommodation else None

    def get_bus_time_effective(self, obj):
        t = obj.bus_time_manual or obj.bus_time_computed
        return t.strftime('%H:%M:%S') if t else None
    
class BusTimeInputSerializer(serializers.Serializer):
    hospital_id = serializers.PrimaryKeyRelatedField(
        queryset=Hospital.objects.all(), source='hospital'
    )
    accommodation_id = serializers.PrimaryKeyRelatedField(
        queryset=Accommodation.objects.all(), source='accommodation'
    )
    appointment_date = serializers.DateField()
    appointment_time = serializers.TimeField()



class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # Replace 'username' with 'email' in the authentication process
        attrs['username'] = attrs.get('email', '')
        return super().validate(attrs)
