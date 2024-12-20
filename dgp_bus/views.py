from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny, BasePermission
from rest_framework.decorators import permission_classes, action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from .models import Hospital, Schedule, Ride, Patient, StaffAdminUser, Accommodation, RidePatient
from .serializers import HospitalSerializer, ScheduleSerializer, PatientSerializer, PatientPublicSerializer, RideSerializer, StaffAdminUserSerializer, RegisterUserSerializer, RidePublicSerializer, ApproveUserSerializer, AccommodationSerializer, SiteUserSerializer
from datetime import date, timedelta
from .permissions import SiteUser

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

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

class RideViewSet(viewsets.ModelViewSet):
    queryset = Ride.objects.all()
    serializer_class = RideSerializer  # Default serializer with all fields

    # Fetch today's rides with all fields
    @action(detail=False, methods=['get'])
    @permission_classes([AllowAny])
    def today(self, request):
        today = date.today()
        rides_today = Ride.objects.filter(date=today).order_by('departure_time')

        # Fetch patients associated with each ride
        rides_with_patients = []
        for ride in rides_today:
            ride_patients = RidePatient.objects.filter(ride=ride)
            patients_data = [
                {
                    'id': rp.patient.id,
                    'name': rp.patient.name,
                    'room': rp.patient.room,
                    'checked_in': rp.checked_in
                } for rp in ride_patients
            ]
            rides_with_patients.append({
                'id': ride.id,
                'departure_time': ride.departure_time,
                'destination': ride.destination.hospital_name,
                'patients': patients_data
            })

        return Response(rides_with_patients)
    
    # Fetch today's rides without the description field
    @action(detail=False, methods=['get'])
    @permission_classes([AllowAny])
    def today_no_desc(self, request):
        today = date.today()
        rides = Ride.objects.filter(date=today).order_by('departure_time')
        serialized_rides = RidePublicSerializer(rides, many=True)
        return Response(serialized_rides.data)

    # Fetch rides for drivers to view
    @action(detail=False, methods=['get'])
    @permission_classes([IsAuthenticated, SiteUser])
    def driver_view(self, request):
        today = date.today()
        rides_today = Ride.objects.filter(date=today)
        serializer = RideSerializer(rides_today, many=True)
        return Response(serializer.data)
    
    # Fetch passengers for a specific ride
    @action(detail=True, methods=['get'], url_path='patients')
    @permission_classes([IsAuthenticated, SiteUser])
    def get_ride_patients(self, request, pk=None):
        try:
            ride = self.get_object()  # Get the specific ride by ID
            ride_patients = RidePatient.objects.filter(ride=ride)  # Fetch patients for the ride
            patients_data = [
                {
                    'id': rp.patient.id,
                    'name': rp.patient.name,
                    'room': rp.patient.room,
                    'checked_in': rp.checked_in
                }
                for rp in ride_patients
            ]
            return Response({'ride_id': ride.id, 'patients': patients_data})
        except Ride.DoesNotExist:
            return Response({'error': 'Ride not found.'}, status=404)


    # Assign a patient to a ride
    @action(detail=True, methods=['post'], url_path='assign-patient')
    @permission_classes([IsAuthenticated, SiteUser])
    def assign_patient_old(self, request, pk=None):
        ride = self.get_object()
        patient_id = request.data.get('patient_id')

        if not patient_id:
            return Response({'error': 'Patient ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            patient = Patient.objects.get(id=patient_id)

            if RidePatient.objects.filter(ride=ride, patient=patient).exists():
                return Response({'error': 'Patient already assigned to this ride.'}, status=status.HTTP_400_BAD_REQUEST)

            if ride.patients.count() >= ride.max_capacity:
                return Response({'error': 'Ride is at full capacity.'}, status=status.HTTP_400_BAD_REQUEST)

            RidePatient.objects.create(ride=ride, patient=patient)
            return Response({'message': 'Patient assigned to ride successfully.'}, status=status.HTTP_201_CREATED)

        except Patient.DoesNotExist:
            return Response({'error': 'Patient not found.'}, status=status.HTTP_404_NOT_FOUND)

    # Toggle patient check-in status for a ride
    @action(detail=True, methods=['patch'], url_path='toggle-check-in')
    @permission_classes([IsAuthenticated, SiteUser])
    def toggle_check_in(self, request, pk=None):
        print("Request data received:", request.data)  # Debugging log for incoming data

        patient_id = request.data.get('patient_id')
        if not patient_id:
            return Response({'error': 'Patient ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        ride = self.get_object()
        try:
            ride_patient = RidePatient.objects.get(ride=ride, patient_id=patient_id)
            ride_patient.checked_in = not ride_patient.checked_in
            ride_patient.save()
            return Response({'checked_in': ride_patient.checked_in}, status=status.HTTP_200_OK)

        except RidePatient.DoesNotExist:
            return Response({'error': 'Patient not found on this ride.'}, status=status.HTTP_404_NOT_FOUND)

