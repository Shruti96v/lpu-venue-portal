from datetime import datetime, date, time
from django.db.models import Q
from .models import Venue, Booking, Equipment


def check_booking_conflict(venue, booking_date, start_time, end_time, exclude_booking_id=None):
    """
    Checks if a booking request conflicts with any existing active booking.
    Returns (has_conflict, list_of_conflicting_bookings)
    """
    if isinstance(booking_date, str):
        booking_date = datetime.strptime(booking_date, "%Y-%m-%d").date()

    active_statuses = ['PENDING', 'APPROVED', 'RESERVED']

    query = Booking.objects.filter(
        venue=venue,
        date=booking_date,
        status__in=active_statuses,
        start_time__lt=end_time,
        end_time__gt=start_time
    )

    if exclude_booking_id:
        query = query.exclude(pk=exclude_booking_id)

    conflicts = list(query)
    return len(conflicts) > 0, conflicts


def get_venue_time_slots(venue, slot_date):
    """
    Returns hourly slot list (8 AM–10 PM) for a venue on a given date.
    Outdoor / ground venues get a wider window.
    Status: available / pending / reserved
    """
    if isinstance(slot_date, str):
        slot_date = datetime.strptime(slot_date, "%Y-%m-%d").date()

    # Outdoor grounds use 6 AM–10 PM; indoor use 8 AM–8 PM
    start_hour = 6 if venue.is_outdoor else 8
    end_hour   = 22 if venue.is_outdoor else 20

    slots = []
    for hour in range(start_hour, end_hour):
        s_time = time(hour, 0)
        e_time = time(hour + 1, 0)

        label_start = s_time.strftime("%I:%M %p").lstrip("0")
        label_end   = e_time.strftime("%I:%M %p").lstrip("0")
        time_label  = f"{label_start} – {label_end}"

        active_bookings = Booking.objects.filter(
            venue=venue,
            date=slot_date,
            status__in=['PENDING', 'APPROVED', 'RESERVED'],
            start_time__lt=e_time,
            end_time__gt=s_time
        )

        if not active_bookings.exists():
            status = 'available'
            booking_info = None
        else:
            b = active_bookings.first()
            if b.status in ('RESERVED', 'APPROVED'):
                status = 'reserved'
            else:
                status = 'pending'

            booking_info = {
                'id': b.id,
                'ref': b.booking_ref,
                'event_name': b.event_name,
                'organizer': b.organizer_name,
                'department': b.department_club,
                'status': b.get_status_display()
            }

        slots.append({
            'hour': hour,
            'start_time': s_time.strftime("%H:%M"),
            'end_time':   e_time.strftime("%H:%M"),
            'label':      time_label,
            'status':     status,
            'booking':    booking_info,
        })

    return slots


def recommend_venues(attendance, required_equipment_ids=None,
                     preferred_date=None, start_time=None, end_time=None):
    """
    Rule-based venue recommendation engine for LPU campus venues.
    Scores each venue on capacity fit, equipment match, and schedule availability.
    """
    attendance = int(attendance or 0)
    required_equipment_ids = required_equipment_ids or []

    equipments = Equipment.objects.filter(id__in=required_equipment_ids)
    equipment_codes = set(equipments.values_list('code', flat=True))

    all_venues = Venue.objects.filter(is_active=True)
    recommendations = []

    for venue in all_venues:
        score = 100
        reasons = []
        is_suitable = True

        # ── Capacity ────────────────────────────────────────────────────────────
        if venue.capacity < attendance:
            score -= 50
            reasons.append(
                f"⚠ Capacity mismatch — venue holds ~{venue.capacity} but you need {attendance}"
            )
            is_suitable = False
        else:
            utilization = round((attendance / venue.capacity) * 100)
            if 50 <= utilization <= 90:
                score += 15
                reasons.append(
                    f"✔ Optimal fit — {attendance} attendees fills {utilization}% of {venue.capacity} capacity"
                )
            elif utilization < 20:
                score -= 8
                reasons.append(
                    f"ℹ Venue is quite large for {attendance} attendees "
                    f"({venue.capacity} capacity — only {utilization}% utilization)"
                )
            else:
                reasons.append(
                    f"✔ Adequate space — {attendance} attendees in {venue.capacity}-capacity venue"
                )

        # ── AV / Equipment match ────────────────────────────────────────────────
        matched, missing = [], []

        if 'projector' in equipment_codes or 'led-screen' in equipment_codes:
            if venue.projector_type:
                score += 10
                matched.append(f"Projection system: {venue.projector_type}")
            else:
                score -= 10
                missing.append("No projection system available")

        if any(c in equipment_codes for c in ['wireless-mic', 'wired-mic', 'speakers']):
            if venue.mic_system_type:
                score += 10
                matched.append(f"Audio: {venue.mic_system_type}")
            else:
                score -= 10
                missing.append("No built-in audio/mic system")

        if 'smart-board' in equipment_codes:
            if venue.has_whiteboard:
                score += 8
                matched.append("Smart/Whiteboard available")
            else:
                score -= 5
                missing.append("No smart board / whiteboard")

        if 'video-conferencing' in equipment_codes:
            if venue.has_video_conferencing:
                score += 15
                matched.append("Video Conferencing unit available")
            else:
                score -= 15
                missing.append("No built-in Video Conferencing")

        if 'stage-lighting' in equipment_codes:
            if venue.has_stage and venue.has_recording:
                score += 12
                matched.append("Stage with lighting & recording setup")
            elif venue.has_stage:
                score += 6
                matched.append("Stage available")
            else:
                score -= 10
                missing.append("No stage for lighting events")

        if 'tent-setup' in equipment_codes or 'generator' in equipment_codes:
            if venue.has_tent_setup:
                score += 15
                matched.append("Tent/Shamiana setup allowed")
            else:
                score -= 20
                missing.append("Tent/Shamiana setup not permitted here")

        if venue.has_ac:
            score += 5
            matched.append("Air Conditioned environment")
        elif not venue.is_outdoor:
            score -= 5

        if matched:
            reasons.append("✔ Matched: " + " | ".join(matched))
        if missing:
            reasons.append("✘ Missing: " + " | ".join(missing))

        # ── Outdoor / Indoor suitability ────────────────────────────────────────
        needs_outdoor = ('tent-setup' in equipment_codes or attendance > 3000)
        if needs_outdoor and venue.is_outdoor:
            score += 15
            reasons.append("✔ Outdoor venue suits large/open-air event")
        elif needs_outdoor and not venue.is_outdoor:
            score -= 10
            reasons.append("ℹ Indoor venue may not suit an open-air or very large event")

        # ── Schedule conflict check ─────────────────────────────────────────────
        has_conflict = False
        if preferred_date and start_time and end_time:
            has_conflict, _ = check_booking_conflict(
                venue, preferred_date, start_time, end_time
            )
            if has_conflict:
                score -= 40
                reasons.append(
                    f"✘ Already booked/pending on {preferred_date} for selected time slot"
                )
            else:
                score += 20
                reasons.append(
                    f"✔ Available on {preferred_date} for your requested slot"
                )

        match_percentage = max(10, min(100, score))
        recommendations.append({
            'venue': venue,
            'match_percentage': match_percentage,
            'score': score,
            'is_suitable': is_suitable and not has_conflict,
            'reasons': reasons,
            'has_conflict': has_conflict,
        })

    recommendations.sort(key=lambda x: x['score'], reverse=True)
    return recommendations
