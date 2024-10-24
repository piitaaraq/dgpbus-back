from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    HospitalViewSet,
    AccommodationViewSet,
    ScheduleViewSet, 
    RideViewSet,  
    AdminApproveUserView,  
    PatientViewSet,
    RegisterUserView,
    public_test_view,
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# Initialize the DefaultRouter for viewsets
router = DefaultRouter()

# Registering viewsets
router.register(r'hospitals', HospitalViewSet)
router.register(r'accommodations', AccommodationViewSet)
router.register(r'schedules', ScheduleViewSet)
router.register(r'rides', RideViewSet, basename='ride')  
router.register(r'patients', PatientViewSet, basename='patient')

# URL patterns
urlpatterns = [
    path('api/test-public/', public_test_view),

    # Include all the viewset routes registered with the router under the 'api/' prefix
    path('api/', include(router.urls)),

    # JWT Token authentication endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  

    # User registration endpoint
    path('api/register/', RegisterUserView.as_view(), name='register_user'),

    # Admin approval endpoint
    path('api/approve-users/', AdminApproveUserView.as_view(), name='approve_user'),  
    path('api/approve-users/<int:staff_id>/', AdminApproveUserView.as_view(), name='approve_user_post'),

]
