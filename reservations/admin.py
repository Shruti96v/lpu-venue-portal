from django.contrib import admin
from .models import Venue, Equipment, Booking, Notification


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name', 'venue_type', 'building_location', 'capacity',
                    'is_outdoor', 'has_ac', 'has_stage', 'is_active')
    list_filter = ('venue_type', 'is_outdoor', 'has_ac', 'has_wifi', 'has_stage',
                   'has_recording', 'has_video_conferencing', 'has_tent_setup', 'is_active')
    search_fields = ('name', 'short_name', 'building_location', 'description')
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'short_name', 'slug', 'venue_type', 'building_location',
                       'floor', 'capacity', 'is_outdoor', 'is_active')
        }),
        ('AV & Facilities', {
            'fields': ('projector_type', 'mic_system_type', 'has_ac', 'has_wifi',
                       'has_whiteboard', 'has_stage', 'has_recording',
                       'has_video_conferencing', 'has_parking', 'has_tent_setup')
        }),
        ('Booking Contact', {
            'fields': ('booking_contact_name', 'booking_contact_phone',
                       'booking_contact_email', 'booking_contact_office')
        }),
        ('Media & Description', {
            'fields': ('description', 'image_url')
        }),
    )


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'category', 'icon_class')
    search_fields = ('name', 'code', 'category')
    prepopulated_fields = {'code': ('name',)}


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_ref', 'event_name', 'venue', 'date',
                    'start_time', 'end_time', 'organizer_name', 'status', 'created_at')
    list_filter = ('status', 'event_type', 'date', 'venue')
    search_fields = ('booking_ref', 'event_name', 'organizer_name',
                     'organizer_id', 'email', 'department_club')
    readonly_fields = ('booking_ref', 'created_at', 'updated_at')
    filter_horizontal = ('required_equipment',)
    fieldsets = (
        ('Booking Reference', {
            'fields': ('booking_ref', 'status', 'admin_notes')
        }),
        ('Event Information', {
            'fields': ('event_name', 'event_type', 'event_description',
                       'venue', 'expected_attendance')
        }),
        ('Schedule', {
            'fields': ('date', 'start_time', 'end_time')
        }),
        ('Organizer Information', {
            'fields': ('organizer_name', 'organizer_id', 'email', 'phone', 'department_club')
        }),
        ('Equipment & Special Requests', {
            'fields': ('required_equipment', 'special_requirements')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'notification_type', 'booking', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read')
    search_fields = ('title', 'message')
