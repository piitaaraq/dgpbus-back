from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    HospitalViewSet,
    AccommodationViewSet,
    ScheduleViewSet,
    get_today_rides, 
    PatientViewSet,
    SiteUserRegisterView,
    SiteUserPasswordResetRequestView,  
    SiteUserPasswordResetConfirmView,  
    SiteUserPasswordResetValidateView,
    SiteUserInviteView,
    SiteUserInviteConfirmView,
    public_test_view,
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# Initialize the DefaultRouter for viewsets
router = DefaultRouter()

# Registering viewsets
router.register(r'hospitals', HospitalViewSet)
router.register(r'accommodations', AccommodationViewSet)
router.register(r'schedules', ScheduleViewSet)
router.register(r'patients', PatientViewSet)  #

# URL patterns
urlpatterns = [
    path('api/test-public/', public_test_view),

    # Include all the viewset routes registered with the router under the 'api/' prefix
    path('api/', include(router.urls)),
    path('api/patients/rides/today/', get_today_rides, name='get_today_rides'),


    # JWT Token authentication endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  

    # User registration endpoints
    path('api/siteusers/register/', SiteUserRegisterView.as_view(), name='siteuser_register'),  # New endpoint

    # Password reset endpoints
    path('api/siteusers/password-reset-request/', SiteUserPasswordResetRequestView.as_view(), name='siteuser_password_reset_request'),
    path('api/siteusers/password-reset-confirm/', SiteUserPasswordResetConfirmView.as_view(), name='siteuser_password_reset_confirm'),
    path('api/siteusers/password-reset-validate/', SiteUserPasswordResetValidateView.as_view(), name='siteuser_password_reset_validate'),

    # User invite endpoints
    path('api/siteusers/invite/', SiteUserInviteView.as_view(), name='siteuser-invite'),
    path('api/siteusers/invite-confirm/', SiteUserInviteConfirmView.as_view(), name='siteuser-invite-confirm'),



]

