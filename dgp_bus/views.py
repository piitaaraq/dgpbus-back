# dgp_bus/views.py
from rest_framework import viewsets, status, generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import permission_classes, action, api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import JSONParser

from .models import Hospital, Schedule, Patient, Appointment, Accommodation, SiteUser as SiteUserModel
from .serializers import (
    HospitalSerializer, ScheduleSerializer, PatientSerializer,
    AppointmentSerializer, AppointmentPublicSerializer,
    StaffAdminUserSerializer, RegisterUserSerializer, ApproveUserSerializer,
    AccommodationSerializer, SiteUserSerializer,
    SiteUserPasswordResetRequestSerializer, SiteUserPasswordResetConfirmSerializer,
    SiteUserInviteSerializer, SiteUserInviteConfirmSerializer,
    BusTimeInputSerializer,
)
from datetime import date, timedelta
from .utils import site_user_password_reset_token, send_password_reset_email, timezone


@api_view(['GET'])
@permission_classes([AllowAny])
def public_test_view(request):
    return Response({"message": "This is public"})


class AccommodationViewSet(viewsets.ModelViewSet):
    queryset = Accommodation.objects.all()
    serializer_class = AccommodationSerializer
    permission_classes = [AllowAny]


class SiteUserRegisterView(APIView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        serializer = SiteUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        user.is_active = False
        user.save()
        return Response({'message': 'User registered successfully. Await admin approval.'}, status=status.HTTP_201_CREATED)

# Password reset request view
class SiteUserPasswordResetRequestView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = SiteUserPasswordResetRequestSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        user = SiteUser.objects.get(email=email)
        send_password_reset_email(user)
        return Response({"detail": "Password reset email sent."}, status=status.HTTP_200_OK)

# Password reset confirm view
class SiteUserPasswordResetConfirmView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = SiteUserPasswordResetConfirmSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password has been reset successfully."}, status=status.HTTP_200_OK)

# Password reset validation view
class SiteUserPasswordResetValidateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        from .utils import verify_signed_reset_data
        signed_data = request.data.get("signed")
        email, token = verify_signed_reset_data(signed_data)

        if not email or not token:
            return Response({"valid": False, "reason": "Ugyldig eller udløbet signatur."}, status=400)

        try:
            user = SiteUserModel.objects.get(email=email)
        except SiteUserModel.DoesNotExist:
            return Response({"valid": False, "reason": "Bruger ikke fundet."}, status=400)

        if not site_user_password_reset_token.check_token(user, token):
            return Response({"valid": False, "reason": "Token udløbet."}, status=400)

        return Response({"valid": True})

class SiteUserInviteView(generics.GenericAPIView):
    serializer_class = SiteUserInviteSerializer
    permission_classes = [IsAuthenticated]  # Only admins should call this endpoint

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Invitation sent."})

class SiteUserInviteConfirmView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = SiteUserInviteConfirmSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Registration complete."})

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]  # default for all other actions

    def get_permissions(self):
        # allow anonymous create; everything else requires staff
        action = getattr(self, 'action', None)
        if action in {'create'}:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_authenticators(self):
        # avoid CSRF/SessionAuth on anonymous POSTs
        action = getattr(self, 'action', None)
        if action in {'create'}:
            return []
        return super().get_authenticators()

    # (optional) keep explicit create for logging
    def create(self, request, *args, **kwargs):
        print("Creating patient (public):", request.data)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.select_related('patient', 'hospital', 'accommodation')
    serializer_class = AppointmentSerializer
    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]  # default

    def get_permissions(self):
        public_actions = {
            'create',
            'calculate_bus_time',
            'freemarker_rides',
            'public_taxi_users',
            'rides_today',
        }
        if getattr(self, 'action', None) in public_actions:
            return [AllowAny()]

        # otherwise: respect self.permission_classes (class default or action override)
        return [perm() for perm in self.permission_classes]

    def get_authenticators(self):
        """Skip SessionAuth/CSRF on public actions."""
        public_actions = {'create', 'calculate_bus_time', 'freemarker_rides', 'public_taxi_users', 'rides_today'}
        action = getattr(self, 'action', None)
        if action in public_actions:
            return []  # no auth schemes -> no CSRF for anonymous POSTs
        return super().get_authenticators()

    # Optional: keep explicit create for logging; not required
    def create(self, request, *args, **kwargs):
        print("Creating appointment (public):", request.data)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)  # serializer.save() runs compute logic
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    # -------- Public reads --------
    @action(detail=False, methods=['get'], url_path='rides-today', permission_classes=[AllowAny])
    def rides_today(self, request):
        today = date.today()
        appts = self.get_queryset().filter(appointment_date=today)
        appts = sorted(
            appts,
            key=lambda a: (
                (a.bus_time_manual or a.bus_time_computed) or timezone.now().time().replace(hour=23, minute=59),
                a.appointment_time,
            ),
        )
        data = AppointmentSerializer(appts, many=True).data
        print("Rides today response:", data)
        return Response(AppointmentSerializer(appts, many=True).data)

    @action(detail=False, methods=['get'], url_path='public-taxi-users', permission_classes=[AllowAny])
    def public_taxi_users_view(self, request):
        today = date.today()
        tomorrow = today + timedelta(days=1)
        qs = self.get_queryset().filter(appointment_date__range=[today, tomorrow])
        appts = [a for a in qs if not (a.bus_time_manual or a.bus_time_computed)]
        return Response(AppointmentPublicSerializer(appts, many=True).data)

    @action(detail=False, methods=['post'], url_path='calculate-bus-time', permission_classes=[AllowAny])
    def calculate_bus_time(self, request):
        ser = BusTimeInputSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        v = ser.validated_data
        bus_time = AppointmentSerializer._compute_bus_time(
            hospital=v['hospital'],
            accommodation=v['accommodation'],
            appointment_date=v['appointment_date'],
            appointment_time=v['appointment_time'],
        )
        return Response({'success': True, 'bus_time': bus_time}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='freemarker-rides', permission_classes=[AllowAny])
    def freemarker_rides(self, request):
        today = date.today()
        qs = self.get_queryset().filter(appointment_date=today)
        qs = [a for a in qs if (a.bus_time_manual or a.bus_time_computed)]
        grouped = {}
        for a in qs:
            key = (a.bus_time_manual or a.bus_time_computed).strftime('%H:%M')
            grouped.setdefault(key, []).append({
                "name": a.patient.name,
                "room": a.patient.room,
            })
        result = [{"departure_time": t, "patients": plist} for t, plist in grouped.items()]
        return Response(result)

    # -------- Staff-only --------
    @action(
        detail=False, methods=['get'], url_path='alle-aftaler',
        permission_classes=[IsAuthenticated]
    )
    def future_appointments(self, request):
        print("DEBUG alle-aftaler HIT")
        today = date.today()
        qs = self.get_queryset().filter(appointment_date__gte=today).order_by('appointment_date', 'appointment_time')
        return Response(AppointmentSerializer(qs, many=True).data, status=status.HTTP_200_OK)
    
    @action(
        detail=False, methods=['get'], url_path='translator-view',
        permission_classes=[IsAuthenticated]
    )
    def translator_view(self, request):
        today = date.today()
        end_date = today + timedelta(days=5)
        qs = (
            self.get_queryset()
            .filter(translator=True, appointment_date__range=[today, end_date])
            .order_by('appointment_date', 'appointment_time')
        )
        return Response(AppointmentSerializer(qs, many=True).data)

    @action(
        detail=False, methods=['get'], url_path='taxi-users',
        permission_classes=[IsAuthenticated]
        )
    def taxi_users_view(self, request):
        today = date.today()
        horizon = today + timedelta(days=120)
        qs = self.get_queryset().filter(appointment_date__range=[today, horizon])
        appts = [a for a in qs if not (a.bus_time_manual or a.bus_time_computed)]
        return Response(AppointmentSerializer(appts, many=True).data)

    @action(detail=True, methods=['patch'], url_path='toggle-status')
    def toggle_status(self, request, pk=None):
        appt = self.get_object()
        appt.status = not appt.status
        appt.save(update_fields=['status'])
        return Response({'id': appt.id, 'status': appt.status}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'], url_path='toggle-taxi')
    def toggle_taxi(self, request, pk=None):
        appt = self.get_object()
        appt.has_taxi = not appt.has_taxi
        appt.save(update_fields=['has_taxi'])
        return Response({'has_taxi': appt.has_taxi}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='find-patient')
    def find_patient(self, request):
        name = request.query_params.get('name')
        room = request.query_params.get('room')
        accommodation = request.query_params.get('accommodation')
        today = date.today()
        if not (name and room and accommodation):
            return Response({'error': 'Name, room, and accommodation are required parameters.'},
                            status=status.HTTP_400_BAD_REQUEST)
        qs = self.get_queryset().filter(
            patient__name=name,
            patient__room=room,
            accommodation__name=accommodation,
            appointment_date__gte=today,
        ).order_by('appointment_date', 'appointment_time')
        if qs.exists():
            return Response(AppointmentSerializer(qs, many=True).data, status=status.HTTP_200_OK)
        return Response({'message': 'No matching patient found with a future appointment.'},
                        status=status.HTTP_404_NOT_FOUND)



@api_view(['GET'])
@permission_classes([AllowAny])
def get_today_rides(request):
    from datetime import date
    from .models import Appointment
    today = date.today()
    qs = (Appointment.objects
          .select_related('patient', 'hospital', 'accommodation')
          .filter(appointment_date=today)
          .order_by('appointment_time'))
    rides = {}
    for a in qs:
        bt = a.bus_time_manual or a.bus_time_computed
        key = bt.strftime('%H:%M') if bt else "Unknown"
        rides.setdefault(key, []).append({
            "id": a.id,
            "name": a.patient.name,
            "room": a.patient.room,
            "hospital": a.hospital.hospital_name,
            "bus_time": key,
            "departure_location": a.departure_location,
            "status": a.status,
            "checked_in": False,
        })
    return Response({"rides": rides})

class HospitalViewSet(viewsets.ModelViewSet):
    queryset = Hospital.objects.all()
    serializer_class = HospitalSerializer
    permission_classes = [AllowAny]

    def list(self, request):
        hospitals = self.get_queryset()
        serializer = self.get_serializer(hospitals, many=True)
        return Response(serializer.data)


class ScheduleViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer

    def list(self, request):
        schedules = self.get_queryset()
        serializer = self.get_serializer(schedules, many=True)
        return Response(serializer.data)


# Optional: if you kept the FBV earlier, you can remove it now
# @api_view(['GET'])
# @permission_classes([AllowAny])
# def get_today_rides(request):
#     ...
