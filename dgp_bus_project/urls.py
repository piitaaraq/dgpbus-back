from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),  # Admin routes

    # Including all the routes from the app (api prefixed at the app level)
    path('', include('dgp_bus.urls')),  # Delegates to app-level urls

    # JWT Token authentication endpoints (can keep these if needed)
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # Endpoint for obtaining JWT
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # Endpoint for refreshing JWT
]
