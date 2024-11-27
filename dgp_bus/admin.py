from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Hospital, Schedule, Accommodation, Patient, StaffAdminUser, SiteUser

# Managing site users
@admin.register(SiteUser)
class SiteUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'is_active', 'date_joined')
    list_filter = ('is_active', 'date_joined')
    search_fields = ('email',)

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


# Customizing the Patient admin
class PatientAdmin(admin.ModelAdmin):
    list_display = ('name', 'room', 'hospital', 'appointment_date', 'appointment_time', 'bus_time', 'translator', 'has_taxi', 'accommodation', 'phone_no')
    list_filter = ('hospital', 'appointment_date', 'translator', 'has_taxi', 'accommodation')  # Filtering options
    search_fields = ('name', 'room', 'phone_no', 'description', 'department')  # Searchable fields
    ordering = ('appointment_date', 'appointment_time')  # Default ordering by appointment date and time
    readonly_fields = ('created_at',)  # Make created_at read-only
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'room', 'phone_no', 'hospital', 'department', 'accommodation')
        }),
        ('Appointment Details', {
            'fields': ('appointment_date', 'appointment_time', 'bus_time', 'translator', 'has_taxi', 'description')
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )

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
admin.site.register(Patient, PatientAdmin)
admin.site.register(StaffAdminUser, StaffAdminUserAdmin)
