from rest_framework import viewsets, status, generics
from rest_framework.permissions import IsAuthenticated, AllowAny, BasePermission
from rest_framework.decorators import permission_classes, action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from .models import Hospital, Schedule, Patient, StaffAdminUser, Accommodation, SiteUser
from .serializers import HospitalSerializer, ScheduleSerializer, PatientSerializer, PatientPublicSerializer,  StaffAdminUserSerializer, RegisterUserSerializer,  ApproveUserSerializer, AccommodationSerializer, SiteUserSerializer, SiteUserPasswordResetRequestSerializer, SiteUserPasswordResetConfirmSerializer, SiteUserInviteSerializer, SiteUserInviteConfirmSerializer
from datetime import date, timedelta
from .permissions import SiteUser
from collections import defaultdict
from rest_framework.decorators import api_view, permission_classes
from .utils import verify_signed_reset_data, site_user_password_reset_token, send_password_reset_email, timezone


@api_view(['GET'])
@permission_classes([AllowAny])
def public_test_view(request):
    return Response({"message": "This is public"})

class AccommodationViewSet(viewsets.ModelViewSet):
    queryset = Accommodation.objects.all()
    serializer_class = AccommodationSerializer
    permission_classes = [AllowAny]  # You can change this based on your needs


class SiteUserRegisterView(APIView):
    """
    Endpoint to register site users (staff who manage patients).
    """
    permission_classes = [AllowAny]  # Open to all for user registration

    def post(self, request, *args, **kwargs):
        from .serializers import SiteUserSerializer  # Import SiteUser serializer

        serializer = SiteUserSerializer(data=request.data)
        if serializer.is_valid():
            # Save the user but set is_active to False for admin approval
            user = serializer.save()
            user.is_active = False
            user.save()

            return Response(
                {'message': 'User registered successfully. Await admin approval.'},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    parser_classes = [JSONParser]

    # Patients with bus_time today
    @action(detail=False, methods=['get'], url_path='rides-today')
    @permission_classes([AllowAny])  # Adjust if needed
    def get_rides_today(self, request):
        today = date.today()
        patients = Patient.objects.filter(
            appointment_date=today,
            bus_time__isnull=False
        ).order_by('bus_time')

        serializer = self.get_serializer(patients, many=True)
        return Response(serializer.data)
    
    # Staff-only access for toggling patient status
    @action(detail=True, methods=['patch'], url_path='toggle-status')
    def toggle_status(self, request, pk=None):
        try:
            patient = self.get_object()
            patient.status = not patient.status
            patient.save()
            return Response({'id': patient.id, 'status': patient.status}, status=status.HTTP_200_OK)
        except Patient.DoesNotExist:
            return Response({'error': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)

    # Staff-only access for translator view
    @action(detail=False, methods=['get'], url_path='translator-view')  # Add custom URL path
    @permission_classes([IsAuthenticated, SiteUser])
    def restricted_translator_view(self, request):
        today = date.today()
        end_date = today + timedelta(days=5)
        patients_needing_translators = Patient.objects.filter(
            translator=True,
            appointment_date__range = [today, end_date]
        )
        serializer = PatientSerializer(patients_needing_translators, many=True)
        return Response(serializer.data)

    # New action to fetch patients with appointments today or later
    @action(detail=False, methods=['get'], url_path='alle-aftaler')
    @permission_classes([IsAuthenticated, SiteUser])
    def future_appointments(self, request):
        today = date.today()
        # Fetch patients with appointments today or in the future
        patients = Patient.objects.filter(appointment_date__gte=today)
        
        # Log the number of patients found
        print(f"Found {patients.count()} patients with appointments today or later.")

        # Serialize the data
        serializer = PatientSerializer(patients, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # Public access version of taxi users view
    @action(detail=False, methods=['get'], url_path='public-taxi-users')
    @permission_classes([AllowAny])  # Allow public access
    def public_taxi_users_view(self, request):
        today = date.today()
        tomorrow = today + timedelta(days=1)
        
        # Same query logic as `taxi_users_view`
        patients_needing_taxis = Patient.objects.filter(
            bus_time__isnull=True,
            appointment_date__range=[today, tomorrow],
        )

        # Use the PublicPatientSerializer to limit exposed fields
        serializer = PatientPublicSerializer(patients_needing_taxis, many=True)
        return Response(serializer.data)   

    # Staff-only access for taxi users view - old version, that assumes the logic for bustime is fully in the backend
    @action(detail=False, methods=['get'], url_path='taxi-users')
    @permission_classes([IsAuthenticated, SiteUser])
    def taxi_users_view(self, request):
        today = date.today()
        tomorrow = today + timedelta(days=120)
        patients_needing_taxis = Patient.objects.filter(
            bus_time__isnull=True,  # we expect that patients without a bus_time need a taxi 
            appointment_date__range=[today, tomorrow],
        )

        # Log to verify if bus_time is actually NULL
        for patient in patients_needing_taxis:
            print(f"Patient {patient.name}: bus_time = {patient.bus_time}")

        serializer = PatientSerializer(patients_needing_taxis, many=True)
        return Response(serializer.data)


    # New action to toggle taxi status
    @action(detail=True, methods=['patch'], url_path='toggle-taxi')
    def toggle_taxi(self, request, pk=None):
        try:
            patient = self.get_object()
            # Toggle the has_taxi status
            patient.has_taxi = not patient.has_taxi
            patient.save()
            return Response({'has_taxi': patient.has_taxi}, status=status.HTTP_200_OK)
        except Patient.DoesNotExist:
            return Response({'error': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)


    # Custom action to find a patient by name, room, and accommodation with future appointments
    @action(detail=False, methods=['get'], url_path='find-patient')
    def find_patient(self, request):
        name = request.query_params.get('name')
        room = request.query_params.get('room')
        accommodation = request.query_params.get('accommodation')
        today = date.today()

        if not (name and room and accommodation):
            return Response({'error': 'Name, room, and accommodation are required parameters.'}, status=status.HTTP_400_BAD_REQUEST)

        patients = Patient.objects.filter(
            name=name,
            room=room,
            accommodation__name=accommodation,
            appointment_date__gte=today  # Filter for today or later
        )

        if patients.exists():
            serializer = PatientSerializer(patients, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'No matching patient found with a future appointment.'}, status=status.HTTP_404_NOT_FOUND)


    # Publicly accessible method for calculating bus times for patients
    @action(detail=False, methods=['post'])
    @permission_classes([AllowAny])  # Allow anyone to access
    def calculate_bus_time(self, request):
        print("Received data for bus time calculation:", request.data)
        serializer = PatientSerializer(data=request.data)
        if serializer.is_valid():
            bus_time = serializer.calculate_bus_time(serializer.validated_data)
            return Response({'success': True, 'bus_time': bus_time})
        print("Serializer errors:", serializer.errors)
        return Response(serializer.errors, status=400)

    # Allow anyone to create (register) a ride (patients)
    @permission_classes([AllowAny])  # Ride creation is open to anyone
    def create(self, request, *args, **kwargs):
        print("Creating patient with data:", request.data)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    # View for use on Freemarker TV system
    @action(detail=False, methods=['get'], url_path='freemarker-rides')
    @permission_classes([AllowAny])  # Allow public access
    def freemarker_rides(self, request):
        today = date.today()
        patients = Patient.objects.filter(
            appointment_date=today,
            bus_time__isnull=False
        ).order_by('bus_time')

        # Group patients by bus_time
        grouped = {}
        for patient in patients:
            key = patient.bus_time.strftime('%H:%M')
            grouped.setdefault(key, []).append({
                "name": patient.name,
                "room": patient.room
            })
        # Convert grouped dict to list of objects
        result = [
            {
                "departure_time": time_str,
                "patients": patients_list
            }
            for time_str, patients_list in grouped.items()
        ]

        return Response(result)



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

@api_view(['GET'])
@permission_classes([AllowAny])
def get_today_rides(request):
    today = date.today()
    patients = Patient.objects.filter(appointment_date=today).order_by('bus_time')

    # Group patients by bus_time
    rides = {}
    for patient in patients:
        key = patient.bus_time.strftime('%H:%M') if patient.bus_time else "Unknown"
        if key not in rides:
            rides[key] = []
        rides[key].append({
            "id": patient.id,
            "name": patient.name,
            "room": patient.room,
            "hospital": patient.hospital.hospital_name,
            "bus_time": key,
            "departure_location": patient.departure_location,
            "status": patient.status,
            "checked_in": False  # You may remove this if unnecessary
        })

    return Response({"rides": rides})

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
            user = SiteUser.objects.get(email=email)
        except SiteUser.DoesNotExist:
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
