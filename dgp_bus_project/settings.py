from pathlib import Path
from datetime import timedelta
from decouple import config, Csv
import os
from dotenv import load_dotenv
load_dotenv()  # only if you're not already loading dotenv


# BASE_DIR is the directory that holds the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Debugging: Test if .env is loaded correctly
try:
    print("Loading .env file...")
    print("SECRET_KEY from .env:", config('DJANGO_SECRET_KEY'))
except Exception as e:
    print("Error loading .env file:", str(e))
    raise


# Environment-specific settings
if config('DJANGO_ENV', default='development') == 'production':
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
else:
    CSRF_COOKIE_SECURE = False
    SESSION_COOKIE_SECURE = False
    SECURE_SSL_REDIRECT = False

# Security and Debug settings
SECRET_KEY = config('DJANGO_SECRET_KEY')
DEBUG = config('DJANGO_DEBUG', default=False, cast=bool)

# Allowed hosts
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*', cast=Csv())
print("ALLOWED_HOSTS:", ALLOWED_HOSTS)

# Installed apps for the project
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    # 'dgp_bus',
    'dgp_bus.apps.DgpBusConfig',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_celery_beat',
]

# Middleware configuration
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Celery setup 
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
# Set a default queue in case a task isn’t explicitly routed
CELERY_TASK_DEFAULT_QUEUE = 'dgp_bus_taxi'

CELERY_TASK_QUEUES = {
    'dgp_bus_taxi': {
        'exchange': 'dgp_bus_taxi',
        'routing_key': 'dgp_bus_taxi',
    },
    'dgp_bus_cleanup': {
        'exchange': 'dgp_bus_cleanup',
        'routing_key': 'dgp_bus_cleanup',
    },
}

CELERY_TASK_ROUTES = {
    'dgp_bus.taxi_email.send_taxi_user_report': {'queue': 'dgp_bus_taxi'},
    'dgp_bus.mailgun_tasks.send_smtp_email': {'queue': 'dgp_bus_taxi'},  # Emails are tied to taxi report
    'dgp_bus.tasks.delete_expired_entries': {'queue': 'dgp_bus_cleanup'},
}


AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',  # Default for admin/staff
    'dgp_bus.backends.SiteUserBackend',  # Custom backend for site users
]

BASE_URL = os.getenv("BASE_URL", "https://bus.patienthjem.dk")
INVITE_TOKEN_EXPIRY = 24 * 60 * 60
FRONTEND_INVITE_URL = f"{BASE_URL}/register-invite"
FRONTEND_RESET_URL = f"{BASE_URL}/reset-password"

#FRONTEND_INVITE_URL = "https://bus.patienthjem.dk/register-invite"

# Token expiration: 24 hours
PASSWORD_RESET_TIMEOUT = 60 * 60 * 24  # 24 hours 

# Frontend reset URL where the user will land to set new password
#FRONTEND_RESET_URL = 'https://bus.patienthjem.dk/reset-password'


AUTH_USER_MODEL = 'dgp_bus.StaffAdminUser'

# Cross-origin resource sharing (CORS) settings
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', cast=Csv())

# REST framework settings, including JWT authentication
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',  # Only restrict specific views
    ),
}

# JWT settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# Root URL configuration
ROOT_URLCONF = 'dgp_bus_project.urls'

# Template settings
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# WSGI application
WSGI_APPLICATION = 'dgp_bus_project.wsgi.application'

# Database settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',  
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', default='3306'),
    }
}

# Password validation settings
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Email settings
from decouple import config

EMAIL_BACKEND = config("EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = config("EMAIL_HOST", default="smtp.mailgun.org")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
EMAIL_HOST_USER = config("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="noreply@example.com")

# Base URL for internal API access (used in Celery tasks)
BASE_URL = config('BASE_URL', default='http://localhost:8000')


# Internationalization and timezone settings
LANGUAGE_CODE = 'da-dk'
TIME_ZONE = 'Europe/Copenhagen'
USE_I18N = True
USE_TZ = True

# Static files settings
STATIC_URL = 'static/'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
