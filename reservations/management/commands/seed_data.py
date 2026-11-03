from datetime import date, datetime, time, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from reservations.models import Venue, Equipment, Booking, Notification


class Command(BaseCommand):
    help = "Seed LPU Campus Venue Reservation System with real LPU infrastructure data."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("🎓 Seeding LPU Campus Venue Reservation System..."))

        # ── 1. Equipment ─────────────────────────────────────────────────────────
        equipment_data = [
            {'name': 'LED / LCD Projector', 'code': 'projector', 'category': 'Display', 'icon_class': 'fa-video'},
            {'name': 'Wireless Handheld Mic', 'code': 'wireless-mic', 'category': 'Audio', 'icon_class': 'fa-microphone'},
            {'name': 'Wired / Podium Mic', 'code': 'wired-mic', 'category': 'Audio', 'icon_class': 'fa-microphone-lines'},
            {'name': 'PA / Surround Speakers', 'code': 'speakers', 'category': 'Audio', 'icon_class': 'fa-volume-high'},
            {'name': 'HDMI / VGA Cable', 'code': 'hdmi', 'category': 'Accessories', 'icon_class': 'fa-plug'},
            {'name': 'Laptop for Presentation', 'code': 'laptop', 'category': 'Computing', 'icon_class': 'fa-laptop'},
            {'name': 'Interactive Smart Board', 'code': 'smart-board', 'category': 'Display', 'icon_class': 'fa-chalkboard-user'},
            {'name': 'Video Conferencing Setup', 'code': 'video-conferencing', 'category': 'Telecom', 'icon_class': 'fa-headset'},
            {'name': 'Stage Lighting / Spotlights', 'code': 'stage-lighting', 'category': 'Lighting', 'icon_class': 'fa-lightbulb'},
            {'name': 'Live Recording / Streaming', 'code': 'recording', 'category': 'Broadcasting', 'icon_class': 'fa-video-slash'},
            {'name': 'Tent / Shamiana Setup', 'code': 'tent-setup', 'category': 'Infrastructure', 'icon_class': 'fa-tent'},
            {'name': 'Generator / Power Backup', 'code': 'generator', 'category': 'Infrastructure', 'icon_class': 'fa-bolt'},
            {'name': 'LED Screen / Jumbotron', 'code': 'led-screen', 'category': 'Display', 'icon_class': 'fa-tv'},
        ]

        created_equipment = {}
        for item in equipment_data:
            eq, _ = Equipment.objects.get_or_create(code=item['code'], defaults=item)
            created_equipment[item['code']] = eq
        self.stdout.write(self.style.SUCCESS(f"  ✔ {len(created_equipment)} Equipment items seeded."))

        # ── 2. LPU Real Campus Venues ─────────────────────────────────────────────
        venues_data = [
            {
                'name': 'Shanti Devi Mittal Auditorium (SDMA)',
                'short_name': 'SDMA',
                'slug': 'sdma-shanti-devi-mittal-auditorium',
                'venue_type': 'AUDITORIUM',
                'building_location': 'University Square, LPU Campus, Phagwara, Punjab',
                'floor': 'Ground Floor',
                'capacity': 5000,
                'is_outdoor': False,
                'projector_type': 'Dual 4K Laser Projection System with Large Screen',
                'mic_system_type': 'Wireless Handheld + Lapel + Podium + Collar Mics',
                'has_ac': True,
                'has_wifi': True,
                'has_whiteboard': False,
                'has_stage': True,
                'has_recording': True,
                'has_video_conferencing': False,
                'has_parking': True,
                'has_tent_setup': False,
                'booking_contact_name': 'Estate & Infrastructure Office, LPU',
                'booking_contact_phone': '01824-404404',
                'booking_contact_email': 'events@lpu.co.in',
                'booking_contact_office': 'Estate Office, Admin Block, LPU Campus',
                'description': (
                    'The Shanti Devi Mittal Auditorium (SDMA) is LPU\'s largest and most prestigious indoor venue, '
                    'named in honour of the university\'s founding family. With a seating capacity of approximately '
                    '5,000 and a grand main stage, SDMA hosts LPU\'s flagship events — Annual Convocations, '
                    'One India National Integration Camp, Aagaz Freshers\' events, and international conferences. '
                    'It is equipped with professional dual 4K laser projection, full PA surround sound, stage lighting, '
                    'live recording & IPTV streaming, and centralized air conditioning.'
                ),
                'image_url': 'https://images.unsplash.com/photo-1540575467063-178a50c2df87?auto=format&fit=crop&w=1000&q=80',
            },
            {
                'name': 'Baldev Raj Mittal Auditorium (BRM)',
                'short_name': 'BRM Auditorium',
                'slug': 'brm-baldev-raj-mittal-auditorium',
                'venue_type': 'AUDITORIUM',
                'building_location': 'Academic Zone, LPU Campus, Phagwara, Punjab',
                'floor': 'Ground Floor',
                'capacity': 1200,
                'is_outdoor': False,
                'projector_type': 'HD Triple Projection System',
                'mic_system_type': 'Wireless Handheld + Podium + Collar Mics',
                'has_ac': True,
                'has_wifi': True,
                'has_whiteboard': False,
                'has_stage': True,
                'has_recording': True,
                'has_video_conferencing': False,
                'has_parking': True,
                'has_tent_setup': False,
                'booking_contact_name': 'Estate & Infrastructure Office, LPU',
                'booking_contact_phone': '01824-404404',
                'booking_contact_email': 'events@lpu.co.in',
                'booking_contact_office': 'Estate Office, Admin Block, LPU Campus',
                'description': (
                    'The Baldev Raj Mittal Auditorium (BRM) is LPU\'s second major indoor auditorium with a seating '
                    'capacity of approximately 1,200. It serves as the primary venue for school-level conferences, '
                    'guest lectures by industry experts, departmental award ceremonies, and mid-scale cultural programmes. '
                    'Equipped with HD triple-projection, full surround PA, professional stage with backstage access, '
                    'and central air conditioning — it is smaller than SDMA but similarly premium in setup.'
                ),
                'image_url': 'https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?auto=format&fit=crop&w=1000&q=80',
            },
            {
                'name': 'Uni Polis Open Stage',
                'short_name': 'Uni Polis',
                'slug': 'uni-polis-open-stage',
                'venue_type': 'OPEN_STAGE',
                'building_location': 'Uni Polis Area, Central LPU Campus, Phagwara, Punjab',
                'floor': 'Open Ground Level',
                'capacity': 3000,
                'is_outdoor': True,
                'projector_type': 'Large Outdoor LED Screen (event-mounted)',
                'mic_system_type': 'High-Power PA System + Wireless Mics',
                'has_ac': False,
                'has_wifi': False,
                'has_whiteboard': False,
                'has_stage': True,
                'has_recording': True,
                'has_video_conferencing': False,
                'has_parking': True,
                'has_tent_setup': False,
                'booking_contact_name': 'Student Welfare Office / Events Cell, LPU',
                'booking_contact_phone': '01824-404404 Ext. 2311',
                'booking_contact_email': 'studentwelfare@lpu.co.in',
                'booking_contact_office': 'Student Welfare Office, Block 32, LPU Campus',
                'description': (
                    'Uni Polis is LPU\'s iconic open-air stage venue at the heart of the campus. It features a '
                    'permanent raised performance stage with dramatic overhead lighting rigs and large outdoor PA speakers. '
                    'This is the go-to venue for Ones with Nature cultural nights, Battle of Bands, comedy shows, inter-school '
                    'talent hunts, Live Vibe music events, and open-mic sessions. The sprawling ground in front '
                    'accommodates a standing + seated crowd of 3,000+. Outdoor LED screens can be arranged for events.'
                ),
                'image_url': 'https://images.unsplash.com/photo-1470229722913-7c0e2dbbafd3?auto=format&fit=crop&w=1000&q=80',
            },
            {
                'name': 'Sports Ground (Near BH-4)',
                'short_name': 'BH-4 Ground',
                'slug': 'sports-ground-bh4',
                'venue_type': 'GROUND',
                'building_location': 'Near Boys Hostel BH-4, LPU Campus, Phagwara, Punjab',
                'floor': 'Open Ground',
                'capacity': 8000,
                'is_outdoor': True,
                'projector_type': 'Portable LED Screen (arrangement required)',
                'mic_system_type': 'Portable PA System (arrangement required)',
                'has_ac': False,
                'has_wifi': False,
                'has_whiteboard': False,
                'has_stage': False,
                'has_recording': False,
                'has_video_conferencing': False,
                'has_parking': True,
                'has_tent_setup': True,
                'booking_contact_name': 'Sports & Physical Education Department, LPU',
                'booking_contact_phone': '01824-404404 Ext. 3200',
                'booking_contact_email': 'sports@lpu.co.in',
                'booking_contact_office': 'Sports Complex Office, Near BH-4, LPU Campus',
                'description': (
                    'The open sports ground near Boys Hostel BH-4 is a large outdoor ground used for sports tournaments, '
                    'inter-university athletic events, large-scale outdoor fests, and hostel zone programmes. '
                    'The ground can accommodate tents/shamianas for temporary event infrastructure. '
                    'AV equipment, generator backup, portable stages, and tent setups are to be arranged separately '
                    'through authorised vendors. Ideal for overnight events, sports days, and mass gatherings.'
                ),
                'image_url': 'https://images.unsplash.com/photo-1574629810360-7efbbe195018?auto=format&fit=crop&w=1000&q=80',
            },
            {
                'name': 'Helipad Ground',
                'short_name': 'Helipad Ground',
                'slug': 'helipad-ground',
                'venue_type': 'GROUND',
                'building_location': 'Helipad Zone, LPU Campus, Phagwara, Punjab',
                'floor': 'Open Ground',
                'capacity': 15000,
                'is_outdoor': True,
                'projector_type': 'Large Outdoor LED Jumbotron (arrangement required)',
                'mic_system_type': 'High-Power Line Array PA System (arrangement required)',
                'has_ac': False,
                'has_wifi': False,
                'has_whiteboard': False,
                'has_stage': False,
                'has_recording': False,
                'has_video_conferencing': False,
                'has_parking': True,
                'has_tent_setup': True,
                'booking_contact_name': 'Estate & Infrastructure Office, LPU',
                'booking_contact_phone': '01824-404404',
                'booking_contact_email': 'estate@lpu.co.in',
                'booking_contact_office': 'Estate Office, Admin Block, LPU Campus',
                'description': (
                    'The Helipad Ground is LPU\'s largest open-air venue — a massive flat ground that can host '
                    'university-scale mega events with 15,000+ attendees. Major festivals like One India\'s grand finale, '
                    'mega concerts, sports opening ceremonies, and national-level gatherings are held here. '
                    'Tent/shamiana infrastructure, temporary stages, generator power setups, and sanitation '
                    'arrangements can be established here. All equipment and infrastructure must be booked through '
                    'the Estate Office. Permission from LPU administration is mandatory for all events.'
                ),
                'image_url': 'https://images.unsplash.com/photo-1492684223066-81342ee5ff30?auto=format&fit=crop&w=1000&q=80',
            },
            {
                'name': 'Seminar Hall — Block 32 (SH-32A)',
                'short_name': 'SH-32A',
                'slug': 'seminar-hall-block-32a',
                'venue_type': 'SEMINAR_HALL',
                'building_location': 'Block 32, Academic Zone, LPU Campus, Phagwara',
                'floor': '1st Floor',
                'capacity': 150,
                'is_outdoor': False,
                'projector_type': 'HD Ceiling-Mounted Projector',
                'mic_system_type': 'Wireless Handheld + Podium Mic',
                'has_ac': True,
                'has_wifi': True,
                'has_whiteboard': True,
                'has_stage': False,
                'has_recording': False,
                'has_video_conferencing': False,
                'has_parking': True,
                'has_tent_setup': False,
                'booking_contact_name': 'School / Department Administrative Office',
                'booking_contact_phone': '01824-404404 Ext. 3201',
                'booking_contact_email': 'schedulingoffice@lpu.co.in',
                'booking_contact_office': 'Block 32 Department Office, LPU Campus — Contact your School Dean / Admin',
                'description': (
                    'Seminar Hall 32-A (SH-32A) in Block 32 is a well-equipped indoor seminar hall seating up to 150 people. '
                    'Used by faculty and student organisations for guest talks, society orientation sessions, departmental '
                    'research presentations, and workshops. Booking is done through the respective School\'s Administrative '
                    'Office or Block 32 management. AC, HD projector, Wi-Fi, and mic system are built in.'
                ),
                'image_url': 'https://images.unsplash.com/photo-1524178232363-1fb2b075b655?auto=format&fit=crop&w=1000&q=80',
            },
            {
                'name': 'Seminar Hall — Block 34 (SH-34B)',
                'short_name': 'SH-34B',
                'slug': 'seminar-hall-block-34b',
                'venue_type': 'SEMINAR_HALL',
                'building_location': 'Block 34, Academic Zone, LPU Campus, Phagwara',
                'floor': '2nd Floor',
                'capacity': 80,
                'is_outdoor': False,
                'projector_type': 'LCD Projector + Smart Screen',
                'mic_system_type': 'Wired Podium Mic + Tabletop Conference Mics',
                'has_ac': True,
                'has_wifi': True,
                'has_whiteboard': True,
                'has_stage': False,
                'has_recording': False,
                'has_video_conferencing': True,
                'has_parking': True,
                'has_tent_setup': False,
                'booking_contact_name': 'Block 34 Department Administrative Office',
                'booking_contact_phone': '01824-404404 Ext. 3401',
                'booking_contact_email': 'schedulingoffice@lpu.co.in',
                'booking_contact_office': 'Block 34, 2nd Floor Admin Desk — Contact your School Dean or HOD',
                'description': (
                    'Seminar Hall 34-B (SH-34B) in Block 34 is a compact, acoustically treated seminar room seating '
                    '80 people. Ideal for doctoral committee reviews, faculty meetings, external expert talks, '
                    'and small group workshops. Equipped with video conferencing capability, making it suitable for '
                    'hybrid sessions with remote speakers. Booking requires prior approval from the HOD or School Dean.'
                ),
                'image_url': 'https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=1000&q=80',
            },
        ]

        created_venues = {}
        for item in venues_data:
            v, created = Venue.objects.get_or_create(slug=item['slug'], defaults=item)
            if not created:
                # Update existing venue with new fields
                for key, val in item.items():
                    setattr(v, key, val)
                v.save()
            created_venues[item['slug']] = v
        self.stdout.write(self.style.SUCCESS(f"  ✔ {len(created_venues)} LPU Venues seeded / updated."))

        # ── 3. Realistic LPU Bookings ─────────────────────────────────────────────
        today = date.today()

        sdma = created_venues['sdma-shanti-devi-mittal-auditorium']
        brm = created_venues['brm-baldev-raj-mittal-auditorium']
        uni_polis = created_venues['uni-polis-open-stage']
        bh4_ground = created_venues['sports-ground-bh4']
        helipad = created_venues['helipad-ground']
        sh32 = created_venues['seminar-hall-block-32a']
        sh34 = created_venues['seminar-hall-block-34b']

        bookings_to_create = [
            {
                'venue': sdma,
                'event_name': '38th Annual Convocation Ceremony — LPU 2026',
                'event_type': 'CONVOCATION',
                'event_description': 'Annual degree conferment ceremony for graduating students across all schools.',
                'organizer_name': 'Dr. Ramesh Bajaj',
                'organizer_id': 'FAC-LPU-0021',
                'email': 'registrar@lpu.co.in',
                'phone': '01824-404404',
                'department_club': 'Office of the Registrar, LPU',
                'date': today + timedelta(days=5),
                'start_time': time(9, 0),
                'end_time': time(17, 0),
                'expected_attendance': 4800,
                'status': 'RESERVED',
                'equip': ['projector', 'wireless-mic', 'speakers', 'stage-lighting', 'recording', 'led-screen'],
                'notes': 'Chief Guest arrival by 8:30 AM. Media access from Press Gate. VVIP seating first 10 rows.',
            },
            {
                'venue': brm,
                'event_name': 'Saksham Guest Lecture — Dr. APJ Abdul Kalam Tribute',
                'event_type': 'GUEST_LECTURE',
                'event_description': 'Annual memorial lecture series inviting eminent scientists and educationists.',
                'organizer_name': 'Prof. Meena Saini',
                'organizer_id': 'FAC-LPU-4410',
                'email': 'meena.saini@lpu.co.in',
                'phone': '+91 98145 23311',
                'department_club': 'School of Physics & Materials Science, LPU',
                'date': today,
                'start_time': time(10, 0),
                'end_time': time(13, 0),
                'expected_attendance': 900,
                'status': 'APPROVED',
                'equip': ['projector', 'wireless-mic', 'speakers', 'recording'],
                'notes': 'Felicitation plaque and memento to be kept at podium.',
            },
            {
                'venue': uni_polis,
                'event_name': 'Live Vibe 2026 — Battle of Bands Night',
                'event_type': 'CULTURAL',
                'event_description': 'Annual inter-university music competition and live performances.',
                'organizer_name': 'Arjun Mehta',
                'organizer_id': 'UID-11014223',
                'email': 'arjun.m@lpu.co.in',
                'phone': '+91 97800 55123',
                'department_club': 'Lovely Cultural Club / Student Welfare Office',
                'date': today,
                'start_time': time(18, 0),
                'end_time': time(22, 0),
                'expected_attendance': 2500,
                'status': 'APPROVED',
                'equip': ['speakers', 'wireless-mic', 'stage-lighting', 'recording', 'led-screen'],
                'notes': 'Sound check by 5:00 PM. Restricted zone behind stage for participants only.',
            },
            {
                'venue': helipad,
                'event_name': 'One India National Integration Camp — Grand Finale',
                'event_type': 'CULTURAL',
                'event_description': 'Closing ceremony of LPU\'s flagship national integration programme with 200+ stalls.',
                'organizer_name': 'Ms. Priya Khanna',
                'organizer_id': 'FAC-LPU-3350',
                'email': 'oneindia@lpu.co.in',
                'phone': '01824-404404 Ext. 2100',
                'department_club': 'Student Welfare Office, LPU',
                'date': today + timedelta(days=10),
                'start_time': time(8, 0),
                'end_time': time(21, 0),
                'expected_attendance': 12000,
                'status': 'RESERVED',
                'equip': ['speakers', 'wireless-mic', 'stage-lighting', 'tent-setup', 'generator', 'led-screen'],
                'notes': 'Full ground tent layout required. 200+ stall infrastructure. Coordinate with Estate Office.',
            },
            {
                'venue': bh4_ground,
                'event_name': 'LPU Inter-Hostel Cricket Tournament — Finals',
                'event_type': 'SPORTS',
                'event_description': 'Final match of the annual inter-hostel cricket championship.',
                'organizer_name': 'Siddharth Nair',
                'organizer_id': 'UID-11029887',
                'email': 'sports.dept@lpu.co.in',
                'phone': '+91 98723 01234',
                'department_club': 'Sports & Physical Education Department',
                'date': today,
                'start_time': time(8, 0),
                'end_time': time(14, 0),
                'expected_attendance': 3000,
                'status': 'PENDING',
                'equip': ['speakers', 'wireless-mic', 'tent-setup'],
                'notes': 'Tents for players and spectators. Ground markings to be done by night before.',
            },
            {
                'venue': sh32,
                'event_name': 'Chanakya Debate Club — Inter-School Policy Debate',
                'event_type': 'CLUB_EVENT',
                'event_description': 'Weekly debates on national policy topics open to all LPU students.',
                'organizer_name': 'Ritika Sharma',
                'organizer_id': 'UID-11031562',
                'email': 'ritika.s@lpu.co.in',
                'phone': '+91 96750 89012',
                'department_club': 'Chanakya Debate & Literary Club, LPU',
                'date': today + timedelta(days=3),
                'start_time': time(14, 0),
                'end_time': time(17, 0),
                'expected_attendance': 120,
                'status': 'PENDING',
                'equip': ['projector', 'wireless-mic', 'wired-mic'],
                'notes': 'Panel of judges to be seated at front table. Timer display required.',
            },
            {
                'venue': sh34,
                'event_name': 'PhD Doctoral Committee Review — CSE Dept.',
                'event_type': 'ACADEMIC',
                'event_description': 'Annual progress review meeting for PhD scholars with external reviewers.',
                'organizer_name': 'Dr. Vijay Kumaravel',
                'organizer_id': 'FAC-LPU-7790',
                'email': 'vijay.k@lpu.co.in',
                'phone': '+91 98140 33456',
                'department_club': 'School of Computer Science & Engineering, LPU',
                'date': today + timedelta(days=1),
                'start_time': time(10, 0),
                'end_time': time(16, 0),
                'expected_attendance': 40,
                'status': 'APPROVED',
                'equip': ['projector', 'video-conferencing', 'wired-mic', 'hdmi'],
                'notes': 'Two external reviewers joining via VC from IIT Delhi. Zoom link to be arranged by IT Dept.',
            },
        ]

        Booking.objects.all().delete()
        Notification.objects.all().delete()
        count = 0
        for data in bookings_to_create:
            equip_codes = data.pop('equip', [])
            notes = data.pop('notes', '')
            b = Booking.objects.create(**data, special_requirements=notes)
            count += 1
            for code in equip_codes:
                if code in created_equipment:
                    b.required_equipment.add(created_equipment[code])

            Notification.objects.create(
                title=f"Event Request: {b.booking_ref}",
                message=f"'{b.event_name}' booked at {b.venue.name} on {b.date.strftime('%d %b %Y')}.",
                notification_type='INFO',
                booking=b
            )

        self.stdout.write(self.style.SUCCESS(f"  ✔ {count} LPU event bookings seeded."))
        self.stdout.write(self.style.SUCCESS("\n🎉 LPU Campus Venue data ready! Run: python manage.py runserver"))
