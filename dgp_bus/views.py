from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny, BasePermission
from rest_framework.decorators import permission_classes, action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from .models import Hospital, Schedule, Ride, Patient, StaffAdminUser, Accommodation 
from .serializers import HospitalSerializer, ScheduleSerializer, PatientSerializer, RideSerializer, StaffAdminUserSerializer, RegisterUserSerializer, RidePublicSerializer, ApproveUserSerializer, AccommodationSerializer
from datetime import date, timedelta
from .permissions import IsStaffOrAdmin, IsAdmin
from django.contrib.auth import authenticate, login
from django.db.models import Q
from django.shortcuts import redirect, render
from django.http import HttpResponse
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer

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


class AdminApproveUserView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]  # Ensure only authenticated admin users can access

    def get(self, request):
        # List all staff/admin members that are inactive (pending approval)
        pending_staff = StaffAdminUser.objects.filter(is_active=False)
        serializer = StaffAdminUserSerializer(pending_staff, many=True)  # Use StaffAdminUserSerializer for listing
        return Response(serializer.data)
    
    def post(self, request, staff_id):
        # Admin approves the staff member by setting is_active to True
        try:
            staff_member = StaffAdminUser.objects.get(id=staff_id, is_active=False)

            # Use the ApproveUserSerializer to update the is_active field
            serializer = ApproveUserSerializer(staff_member, data={"is_active": True}, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)  # Return the updated user info

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except StaffAdminUser.DoesNotExist:
            return Response({"error": "Staff member not found or already active."}, status=status.HTTP_404_NOT_FOUND)


class RegisterUserView(APIView):
    def post(self, request):
        serializer = RegisterUserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'User registered successfully. Await admin approval.'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        # Only allow access if the user is an admin
        return request.user.is_authenticated and request.user.is_admin

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    parser_classes = [JSONParser]

    # Staff-only access for translator view
    @action(detail=False, methods=['get'], url_path='translator-view')  # Add custom URL path
    @permission_classes([IsAuthenticated, IsStaffOrAdmin])
    def restricted_translator_view(self, request):
        today = date.today()
        end_date = today + timedelta(days=5)
        patients_needing_translators = Patient.objects.filter(
            translator=True,
            appointment_date__range = [today, end_date]
        )
        serializer = PatientSerializer(patients_needing_translators, many=True)
        return Response(serializer.data)

   

    # Staff-only access for taxi users view - old version, that assumes the logic for bustime is fully in the backend
    @action(detail=False, methods=['get'], url_path='taxi-users')
    @permission_classes([IsAuthenticated, IsStaffOrAdmin])
    def taxi_users_view(self, request):
        today = date.today()
        tomorrow = today + timedelta(days=1)
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

    @action(detail=False, methods=['get'])
    @permission_classes([IsAuthenticated, IsStaffOrAdmin])  # Public access allowed
    def today(self, request):
        today = date.today()
        rides = Ride.objects.filter(date=today).order_by('departure_time', 'hospital_name')
        serialized_rides = self.get_serializer(rides, many=True)
        return Response(serialized_rides.data)

    # New action to fetch today's rides without the description field
    @action(detail=False, methods=['get'])
    @permission_classes([AllowAny])  # Public access allowed
    def today_no_desc(self, request):
        today = date.today()
        rides = Ride.objects.filter(date=today).order_by('departure_time')
        serialized_rides = RidePublicSerializer(rides, many=True)  # Use the serializer without description
        return Response(serialized_rides.data)

    @action(detail=False, methods=['get'])
    @permission_classes([IsAuthenticated, IsStaffOrAdmin])  # Ensure drivers are authenticated
    def driver_view(self, request):
        today = date.today()
        rides_today = Ride.objects.filter(date=today)
        serializer = RideSerializer(rides_today, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'])
    @permission_classes([IsAuthenticated])
    def toggle_status(self, request, pk=None):
        ride = self.get_object()
        ride.status = not ride.status
        ride.save()
        return Response({'status': ride.status})

