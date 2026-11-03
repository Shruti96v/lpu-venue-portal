import random
import string
from django.db import models
from django.utils import timezone


class Equipment(models.Model):
    name = models.CharField(max_length=100)
    code = models.SlugField(max_length=100, unique=True)
    category = models.CharField(max_length=50, default="AV Equipment")
    icon_class = models.CharField(max_length=50, default="fa-plug")

    class Meta:
        verbose_name_plural = "Equipment"
        ordering = ['name']

    def __str__(self):
        return self.name


class Venue(models.Model):
    VENUE_TYPE_CHOICES = [
        ('AUDITORIUM', 'Auditorium'),
        ('OPEN_STAGE', 'Open Stage / Outdoor Stage'),
        ('GROUND', 'Open Ground / Sports Ground'),
        ('SEMINAR_HALL', 'Seminar Hall'),
        ('CONFERENCE_ROOM', 'Conference Room'),
        ('OTHER', 'Other'),
    ]

    name = models.CharField(max_length=150, unique=True)
    short_name = models.CharField(max_length=50, blank=True, help_text="Abbreviated name e.g. SDMA, BRM, Uni Polis")
    slug = models.SlugField(max_length=150, unique=True)
    venue_type = models.CharField(max_length=30, choices=VENUE_TYPE_CHOICES, default='AUDITORIUM')
    building_location = models.CharField(max_length=200)
    floor = models.CharField(max_length=50, default="Ground Floor")
    capacity = models.PositiveIntegerField(help_text="Approximate maximum capacity")
    is_outdoor = models.BooleanField(default=False, verbose_name="Outdoor Venue")

    # Specification details
    projector_type = models.CharField(max_length=100, blank=True, help_text="e.g. 4K Laser Projector, Not Available")
    mic_system_type = models.CharField(max_length=100, blank=True, help_text="e.g. Wireless Handheld, PA System")
    has_ac = models.BooleanField(default=False, verbose_name="Air Conditioning (AC)")
    has_wifi = models.BooleanField(default=False, verbose_name="Wi-Fi")
    has_whiteboard = models.BooleanField(default=False, verbose_name="Whiteboard")
    has_stage = models.BooleanField(default=False, verbose_name="Stage / Raised Platform")
    has_recording = models.BooleanField(default=False, verbose_name="Recording / Livestream Facilities")
    has_video_conferencing = models.BooleanField(default=False, verbose_name="Video Conferencing Unit")
    has_parking = models.BooleanField(default=True, verbose_name="Parking Nearby")
    has_tent_setup = models.BooleanField(default=False, verbose_name="Tent / Shamiana Setup Allowed")

    # Contact for Booking
    booking_contact_name = models.CharField(max_length=150, blank=True, help_text="Contact person for booking this venue")
    booking_contact_phone = models.CharField(max_length=30, blank=True, help_text="Phone number to call for booking")
    booking_contact_email = models.EmailField(blank=True, help_text="Email for booking inquiries")
    booking_contact_office = models.CharField(max_length=200, blank=True, help_text="Office or department to approach")

    description = models.TextField(blank=True)
    image_url = models.CharField(max_length=500, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-capacity', 'name']

    def __str__(self):
        return f"{self.name} (~{self.capacity} capacity)"

    def get_features_list(self):
        features = []
        if self.is_outdoor:
            features.append("Outdoor Venue")
        else:
            features.append("Indoor Venue")
        if self.has_ac:
            features.append("Air Conditioned")
        if self.has_wifi:
            features.append("Wi-Fi Available")
        if self.has_whiteboard:
            features.append("Whiteboard")
        if self.has_stage:
            features.append("Stage / Raised Platform")
        if self.has_recording:
            features.append("Live Recording & Streaming")
        if self.has_video_conferencing:
            features.append("Video Conferencing")
        if self.has_tent_setup:
            features.append("Tent / Shamiana Setup Allowed")
        if self.has_parking:
            features.append("Parking Available Nearby")
        return features


class Booking(models.Model):
    EVENT_TYPE_CHOICES = [
        ('GUEST_LECTURE', 'Guest Lecture / Talk'),
        ('CLUB_EVENT', 'Club Event / Society Activity'),
        ('WORKSHOP', 'Workshop / Seminar'),
        ('CONFERENCE', 'Academic Conference / Symposium'),
        ('CULTURAL', 'Cultural Event / Fest / Talent Show'),
        ('SPORTS', 'Sports Event / Tournament'),
        ('CONVOCATION', 'Convocation / Award Ceremony'),
        ('RELIGIOUS', 'Religious / Social Gathering'),
        ('ACADEMIC', 'Examination / Academic Activity'),
        ('OTHER', 'Other Event'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('RESERVED', 'Reserved (Confirmed)'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]

    booking_ref = models.CharField(max_length=20, unique=True, editable=False)
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='bookings')

    # Event Info
    event_name = models.CharField(max_length=200)
    event_description = models.TextField(blank=True)
    event_type = models.CharField(max_length=30, choices=EVENT_TYPE_CHOICES, default='CLUB_EVENT')

    # Organizer Info
    organizer_name = models.CharField(max_length=150)
    organizer_id = models.CharField(max_length=50, help_text="Student UID or Faculty Employee ID")
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    department_club = models.CharField(max_length=150, help_text="School / Department / Club Name at LPU")

    # Schedule & Capacity
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    expected_attendance = models.PositiveIntegerField()

    # Requirements
    required_equipment = models.ManyToManyField(Equipment, blank=True, related_name='bookings')
    special_requirements = models.TextField(blank=True)

    # Status & Admin
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    admin_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-start_time']

    def save(self, *args, **kwargs):
        if not self.booking_ref:
            prefix = "LPU-"
            year = timezone.now().strftime("%Y")
            random_digits = "".join(random.choices(string.digits, k=5))
            self.booking_ref = f"{prefix}{year}-{random_digits}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.booking_ref} — {self.event_name} @ {self.venue.name} on {self.date}"

    @property
    def is_active_booking(self):
        return self.status in ['PENDING', 'APPROVED', 'RESERVED']


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('INFO', 'Information'),
        ('SUCCESS', 'Success'),
        ('WARNING', 'Warning'),
        ('DANGER', 'Danger / Alert'),
    ]

    title = models.CharField(max_length=150)
    message = models.TextField()
    notification_type = models.CharField(max_length=10, choices=NOTIFICATION_TYPES, default='INFO')
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.notification_type}] {self.title}"
