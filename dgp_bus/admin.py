# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Hospital, Schedule, Accommodation,
    Patient, Appointment,     # <-- import Appointment
    StaffAdminUser, SiteUser
)
from datetime import datetime, timedelta
from .utils import send_invite_email

@admin.action(description="Send invite email")
def send_invite(modeladmin, request, queryset):
    for user in queryset:
        send_invite_email(user.email)

# --- SiteUser ---
@admin.register(SiteUser)
class SiteUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'is_active', 'is_frontdesk', 'date_joined')
    list_filter = ('is_active', 'is_frontdesk', 'date_joined')
    search_fields = ('email',)
    actions = [send_invite]
    exclude = ('password',)
    def get_changeform_initial_data(self, request):
        return {'is_active': False}

# --- Hospital ---
@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ('hospital_name', 'address')
    search_fields = ('hospital_name', 'address')
    ordering = ('hospital_name',)

# --- Schedule ---
@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('departure_location', 'destination', 'day_of_week', 'departure_time')
    list_filter = ('day_of_week', 'destination')
    search_fields = ('departure_location', 'destination__hospital_name')
    ordering = ('day_of_week', 'departure_time')

# --- Accommodation ---
@admin.register(Accommodation)
class AccommodationAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)

# --- Patient (personal-only now) ---
@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'last_name', 'day_of_birth', 'phone_no', 'room',
        # include default_accommodation only if you added it:
        'default_accommodation',
        'created_at',
    )
    search_fields = ('name', 'last_name', 'phone_no', 'room')
    # include default_accommodation here only if present on model:
    list_filter = ('default_accommodation',)
    ordering = ('name', 'last_name')
    readonly_fields = ('created_at',)

    fieldsets = (
        ('Personal info', {
            'fields': (
                'name', 'last_name', 'day_of_birth', 'phone_no', 'room',
                # include default_accommodation only if present:
                'default_accommodation',
            )
        }),
        ('Metadata', {'fields': ('created_at',)}),
    )

# --- Appointment (all appointment-scoped fields) ---
@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        'patient', 'hospital', 'accommodation',
        'appointment_date', 'appointment_time',
        'bus_time_manual', 'bus_time_computed',
        'translator', 'has_taxi', 'wheelchair', 'trolley', 'companion',
        'status',
        'created_at',
    )
    list_filter = (
        'hospital', 'accommodation', 'appointment_date',
        'translator', 'has_taxi', 'status', 'wheelchair', 'trolley', 'companion',
    )
    search_fields = (
        'patient__name', 'patient__last_name', 'patient__room',
        'department', 'description',
    )
    ordering = ('appointment_date', 'appointment_time')
    readonly_fields = ('created_at',)
    autocomplete_fields = ('patient', 'hospital', 'accommodation')

    fieldsets = (
        ('Links', {'fields': ('patient', 'hospital', 'accommodation')}),
        ('Appointment details', {
            'fields': (
                'appointment_date', 'appointment_time',
                'bus_time_manual', 'bus_time_computed',
                'status', 'translator', 'has_taxi',
                'wheelchair', 'trolley', 'companion',
                'department', 'description', 'departure_location',
            )
        }),
        ('Metadata', {'fields': ('created_at',)}),
    )

    actions = ['recalculate_bus_time']

    def recalculate_bus_time(self, request, queryset):
        """Recalculate bus_time_computed for selected appointments (keeps manual overrides)."""
        updated = 0
        for appt in queryset.select_related('hospital', 'accommodation', 'patient'):
            # Keep manual if set
            if appt.bus_time_manual:
                continue

            bt = self._compute_bus_time(appt)
            if bt != appt.bus_time_computed:
                appt.bus_time_computed = bt
                appt.save(update_fields=['bus_time_computed'])
                updated += 1
        self.message_user(request, f"✅ Recalculated bus time for {updated} appointment(s).")

    recalculate_bus_time.short_description = "Recalculate bus time (computed) for selected appointments"

    # Same logic you had, adapted to Appointment
    def _compute_bus_time(self, appt):
        hospital = appt.hospital
        # prefer per-appointment accommodation, no fallback here (stay explicit in admin)
        accommodation = appt.accommodation
        if not (hospital and accommodation and appt.appointment_date and appt.appointment_time):
            return None

        if hospital.id in [1, 3, 7] and accommodation.name == 'Det grønlandske Patienthjem':
            day_of_week = appt.appointment_date.strftime('%A')
            schedule_hospital_id = 1 if hospital.id in [3, 7] else hospital.id
            schedules = Schedule.objects.filter(
                destination_id=schedule_hospital_id,
                day_of_week=day_of_week
            )

            latest_departure = (
                datetime.combine(appt.appointment_date, appt.appointment_time)
                - timedelta(minutes=30)
            ).time()

            suitable = None
            for s in schedules:
                if s.departure_time <= latest_departure and (
                    suitable is None or s.departure_time > suitable.departure_time
                ):
                    suitable = s
            return suitable.departure_time if suitable else None
        return None

# --- StaffAdminUser ---
@admin.register(StaffAdminUser)
class StaffAdminUserAdmin(UserAdmin):
    list_display = ('email', 'role', 'is_staff', 'is_admin', 'is_active', 'date_joined', 'last_login')
    list_filter = ('role', 'is_staff', 'is_admin', 'is_active')
    search_fields = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('role',)}),
        ('Permissions', {'fields': ('is_staff', 'is_admin', 'is_active')}),
        ('Timestamps', {'fields': ('date_joined', 'last_login')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role', 'is_staff', 'is_admin', 'is_active'),
        }),
    )
    readonly_fields = ('date_joined', 'last_login')
    ordering = ('email',)
    filter_horizontal = ()
