from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Hospital, Schedule, Accommodation, Patient, StaffAdminUser, SiteUser
from datetime import datetime, timedelta
from .utils import send_invite_email  # Import the invite email function

@admin.action(description="Send invite email")
def send_invite(modeladmin, request, queryset):
    for user in queryset:
        send_invite_email(user.email)

# Managing site users
@admin.register(SiteUser)
class SiteUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'is_active', 'is_frontdesk', 'date_joined')
    list_filter = ('is_active', 'is_frontdesk', 'date_joined')
    search_fields = ('email',)
    actions = [send_invite] 

    # Fully disable password fields:
    exclude = ('password',)

    # Optional: make sure is_active defaults to False when creating
    def get_changeform_initial_data(self, request):
        return {'is_active': False}


# Customizing the Hospital admin
class HospitalAdmin(admin.ModelAdmin):
    list_display = ('hospital_name', 'address')  # Columns in the list view
    search_fields = ('hospital_name', 'address')  # Search functionality
    ordering = ('hospital_name',)  # Default ordering

# Customizing the Schedule admin
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('departure_location', 'destination', 'day_of_week', 'departure_time')
    list_filter = ('day_of_week', 'destination')  # Enable filtering
    search_fields = ('departure_location', 'destination__hospital_name')  # Search in related field
    ordering = ('day_of_week', 'departure_time')  # Order by day and time

# Customizing the Accommodation admin
class AccommodationAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)


class PatientAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'room', 'hospital', 'appointment_date', 'appointment_time',
        'bus_time', 'translator', 'has_taxi', 'accommodation', 'phone_no', 'created_at'
    )
    list_filter = (
        'hospital', 'appointment_date', 'translator', 'has_taxi', 'accommodation'
    )
    search_fields = ('name', 'room', 'phone_no', 'description', 'department')
    ordering = ('appointment_date', 'appointment_time')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name', 'room', 'phone_no', 'hospital', 'department',
                'accommodation', 'wheelchair', 'trolley', 'companion'
            )
        }),
        ('Appointment Details', {
            'fields': (
                'appointment_date', 'appointment_time', 'bus_time',
                'translator', 'has_taxi', 'description'
            )
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )

    actions = ['recalculate_bus_time']

    def recalculate_bus_time(self, request, queryset):
        updated = 0
        for patient in queryset:
            new_time = self.calculate_bus_time(patient)
            if new_time:
                patient.bus_time = new_time
                patient.save()
                updated += 1
        self.message_user(request, f"✅ Recalculated bus time for {updated} patient(s).")
    
    recalculate_bus_time.short_description = "Recalculate bus time for selected patients"

    def calculate_bus_time(self, patient):
        # Bus time logic copied from serializer
        if (
            patient.hospital.id in [1, 3, 7] and 
            patient.accommodation and 
            patient.accommodation.name == 'Det grønlandske Patienthjem'
        ):
            day_of_week = patient.appointment_date.strftime('%A')
            schedule_hospital_id = 1 if patient.hospital.id in [3, 7] else patient.hospital.id

            schedules = Schedule.objects.filter(
                destination_id=schedule_hospital_id,
                day_of_week=day_of_week
            )

            suitable_schedule = None
            for schedule in schedules:
                latest_departure = (
                    datetime.combine(patient.appointment_date, patient.appointment_time)
                    - timedelta(minutes=30)
                ).time()

                if schedule.departure_time <= latest_departure:
                    if not suitable_schedule or schedule.departure_time > suitable_schedule.departure_time:
                        suitable_schedule = schedule

            return suitable_schedule.departure_time if suitable_schedule else None
        return None


class StaffAdminUserAdmin(UserAdmin):
    # Fields to display in the list view
    list_display = ('email', 'role', 'is_staff', 'is_admin', 'is_active', 'date_joined', 'last_login')
    
    # Fields to filter in the sidebar
    list_filter = ('role', 'is_staff', 'is_admin', 'is_active')
    
    # Fields to search
    search_fields = ('email',)
    
    # Fields for the add and edit forms
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
    # Make date_joined read-only
    readonly_fields = ('date_joined', 'last_login')

    # Ordering and additional settings
    ordering = ('email',)

    # Remove 'groups' and 'user_permissions' from filter_horizontal
    filter_horizontal = ()



# Register the models with the custom ModelAdmin
admin.site.register(Hospital, HospitalAdmin)
admin.site.register(Schedule, ScheduleAdmin)
admin.site.register(Accommodation, AccommodationAdmin)
admin.site.register(StaffAdminUser, StaffAdminUserAdmin)
admin.site.register(Patient, PatientAdmin)
