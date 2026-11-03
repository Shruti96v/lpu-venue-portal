from datetime import date, time, timedelta
from django.test import TestCase
from django.core.exceptions import ValidationError
from reservations.models import Venue, Equipment, Booking, Notification
from reservations.forms import BookingForm
from reservations.utils import check_booking_conflict, get_venue_time_slots, recommend_venues

class CampusVenueSystemTests(TestCase):
    def setUp(self):
        # Create sample venue
        self.venue = Venue.objects.create(
            name="Test Auditorium",
            slug="test-auditorium",
            building_location="Building A",
            floor="Ground Floor",
            capacity=200,
            projector_type="4K Laser Projector",
            mic_system_type="Wireless Handheld",
            has_ac=True,
            has_wifi=True,
            has_whiteboard=True,
            has_stage=True,
            has_recording=True,
            has_video_conferencing=True
        )

        # Create equipment
        self.eq_projector = Equipment.objects.create(name="Projector", code="projector")
        self.eq_mic = Equipment.objects.create(name="Wireless Mic", code="wireless-mic")

        self.today = date.today()

    def test_venue_creation(self):
        self.assertEqual(self.venue.capacity, 200)
        self.assertTrue(self.venue.has_ac)
        self.assertIn("Air Conditioned", self.venue.get_features_list())

    def test_booking_auto_reference_creation(self):
        booking = Booking.objects.create(
            venue=self.venue,
            event_name="AI Workshop",
            event_type="WORKSHOP",
            organizer_name="John Doe",
            organizer_id="FAC-123",
            email="john@campus.edu",
            phone="+91 9876543210",
            department_club="AI Club",
            date=self.today,
            start_time=time(10, 0),
            end_time=time(12, 0),
            expected_attendance=150,
            status="APPROVED"
        )
        self.assertTrue(booking.booking_ref.startswith("BK-"))

    def test_conflict_detection_logic(self):
        # Create an active booking from 10:00 to 12:00
        Booking.objects.create(
            venue=self.venue,
            event_name="Existing Lecture",
            event_type="GUEST_LECTURE",
            organizer_name="Jane Doe",
            organizer_id="FAC-456",
            email="jane@campus.edu",
            phone="+91 9876543210",
            department_club="Physics Dept",
            date=self.today,
            start_time=time(10, 0),
            end_time=time(12, 0),
            expected_attendance=100,
            status="APPROVED"
        )

        # 1. Overlapping start (11:00 to 13:00) -> Should conflict
        has_conflict, conflicts = check_booking_conflict(self.venue, self.today, time(11, 0), time(13, 0))
        self.assertTrue(has_conflict)
        self.assertEqual(len(conflicts), 1)

        # 2. Non-overlapping time (14:00 to 16:00) -> Should NOT conflict
        has_conflict, conflicts = check_booking_conflict(self.venue, self.today, time(14, 0), time(16, 0))
        self.assertFalse(has_conflict)

    def test_booking_form_validation(self):
        # 1. Test Attendance Exceeds Capacity
        form_data_exceed = {
            'venue': self.venue.id,
            'event_name': 'Overcrowded Event',
            'event_type': 'CULTURAL',
            'organizer_name': 'Mark Smith',
            'organizer_id': 'STU-999',
            'email': 'mark@campus.edu',
            'phone': '+91 9876543210',
            'department_club': 'Drama Club',
            'date': self.today.strftime('%Y-%m-%d'),
            'start_time': '10:00',
            'end_time': '12:00',
            'expected_attendance': 500,  # Exceeds venue capacity of 200!
        }
        form = BookingForm(data=form_data_exceed)
        self.assertFalse(form.is_valid())
        self.assertIn('expected_attendance', form.errors)

        # 2. Test Invalid Time Order (End before start)
        form_data_time = form_data_exceed.copy()
        form_data_time['expected_attendance'] = 100
        form_data_time['start_time'] = '14:00'
        form_data_time['end_time'] = '11:00'  # Invalid!
        form = BookingForm(data=form_data_time)
        self.assertFalse(form.is_valid())
        self.assertIn('end_time', form.errors)

    def test_smart_venue_recommendation(self):
        results = recommend_venues(
            attendance=150,
            required_equipment_ids=[self.eq_projector.id, self.eq_mic.id],
            preferred_date=self.today,
            start_time=time(14, 0),
            end_time=time(16, 0)
        )
        self.assertTrue(len(results) > 0)
        top_recommendation = results[0]
        self.assertEqual(top_recommendation['venue'], self.venue)
        self.assertTrue(top_recommendation['is_suitable'])
