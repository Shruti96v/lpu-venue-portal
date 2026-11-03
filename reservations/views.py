from datetime import date, datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count
from django.views.decorators.http import require_POST

from .models import Venue, Booking, Equipment, Notification
from .forms import BookingForm, VenueFilterForm, RecommendationRequestForm
from .utils import check_booking_conflict, get_venue_time_slots, recommend_venues

def dashboard_view(request):
    today = date.today()
    
    total_venues = Venue.objects.filter(is_active=True).count()
    pending_requests = Booking.objects.filter(status='PENDING').count()
    upcoming_events = Booking.objects.filter(
        status__in=['APPROVED', 'RESERVED'],
        date__gte=today
    ).count()
    
    # Calculate available venues today (venues without a full day lock)
    all_venues = Venue.objects.filter(is_active=True)
    available_venues_today_count = 0
    venue_schedule_today = []
    
    for venue in all_venues:
        slots = get_venue_time_slots(venue, today)
        booked_hours = sum(1 for s in slots if s['status'] in ['pending', 'reserved'])
        if booked_hours < len(slots):
            available_venues_today_count += 1
            
        venue_schedule_today.append({
            'venue': venue,
            'slots': slots,
            'booked_count': booked_hours,
            'free_count': len(slots) - booked_hours
        })
        
    recent_bookings = Booking.objects.all()[:6]
    unread_notifications = Notification.objects.filter(is_read=False)[:5]
    
    context = {
        'total_venues': total_venues,
        'available_venues_today': available_venues_today_count,
        'pending_requests': pending_requests,
        'upcoming_events': upcoming_events,
        'venue_schedule_today': venue_schedule_today,
        'recent_bookings': recent_bookings,
        'unread_notifications': unread_notifications,
        'today': today,
    }
    return render(request, 'reservations/dashboard.html', context)


def venue_list_view(request):
    venues = Venue.objects.filter(is_active=True)
    form = VenueFilterForm(request.GET)
    
    if form.is_valid():
        search = form.cleaned_data.get('search')
        min_capacity = form.cleaned_data.get('min_capacity')
        has_ac = form.cleaned_data.get('has_ac')
        has_wifi = form.cleaned_data.get('has_wifi')
        has_stage = form.cleaned_data.get('has_stage')
        has_video_conferencing = form.cleaned_data.get('has_video_conferencing')
        
        if search:
            venues = venues.filter(
                Q(name__icontains=search) |
                Q(building_location__icontains=search) |
                Q(description__icontains=search)
            )
        if min_capacity:
            venues = venues.filter(capacity__gte=min_capacity)
        if has_ac:
            venues = venues.filter(has_ac=True)
        if has_wifi:
            venues = venues.filter(has_wifi=True)
        if has_stage:
            venues = venues.filter(has_stage=True)
        if has_video_conferencing:
            venues = venues.filter(has_video_conferencing=True)

        is_outdoor = form.cleaned_data.get('is_outdoor')
        has_stage = form.cleaned_data.get('has_stage')
        has_tent_setup = form.cleaned_data.get('has_tent_setup')
        venue_type = form.cleaned_data.get('venue_type')

        if is_outdoor:
            venues = venues.filter(is_outdoor=True)
        if has_stage:
            venues = venues.filter(has_stage=True)
        if has_tent_setup:
            venues = venues.filter(has_tent_setup=True)
        if venue_type:
            venues = venues.filter(venue_type=venue_type)

        # also filter by short_name / name for search
        if search:
            venues = venues | Venue.objects.filter(
                is_active=True
            ).filter(
                Q(short_name__icontains=search)
            )
            venues = venues.distinct()

    context = {
        'venues': venues,
        'filter_form': form,
    }
    return render(request, 'reservations/venue_list.html', context)


def venue_detail_view(request, slug):
    venue = get_object_or_404(Venue, slug=slug, is_active=True)
    today = date.today()
    selected_date_str = request.GET.get('date', today.strftime('%Y-%m-%d'))
    
    try:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = today
        
    slots = get_venue_time_slots(venue, selected_date)
    upcoming_bookings = Booking.objects.filter(
        venue=venue,
        date__gte=today,
        status__in=['APPROVED', 'RESERVED', 'PENDING']
    )[:5]
    
    context = {
        'venue': venue,
        'slots': slots,
        'selected_date': selected_date,
        'upcoming_bookings': upcoming_bookings,
    }
    return render(request, 'reservations/venue_detail.html', context)


def venue_compare_view(request):
    venues = Venue.objects.filter(is_active=True)
    all_equipment = Equipment.objects.all()
    
    selected_ids = request.GET.getlist('venue_ids')
    if selected_ids:
        compare_venues = venues.filter(id__in=selected_ids)
    else:
        compare_venues = venues[:4]
        
    context = {
        'venues': venues,
        'compare_venues': compare_venues,
        'all_equipment': all_equipment,
    }
    return render(request, 'reservations/venue_compare.html', context)


def calendar_view(request):
    venues = Venue.objects.filter(is_active=True)
    selected_venue_id = request.GET.get('venue')
    selected_date_str = request.GET.get('date', date.today().strftime('%Y-%m-%d'))
    
    if selected_venue_id:
        current_venue = get_object_or_404(Venue, pk=selected_venue_id)
    else:
        current_venue = venues.first()
        
    try:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = date.today()
        
    slots = get_venue_time_slots(current_venue, selected_date) if current_venue else []
    
    context = {
        'venues': venues,
        'current_venue': current_venue,
        'selected_date': selected_date,
        'slots': slots,
    }
    return render(request, 'reservations/calendar.html', context)


def api_venue_slots(request):
    venue_id = request.GET.get('venue_id')
    date_str = request.GET.get('date')
    
    if not venue_id or not date_str:
        return JsonResponse({'error': 'Missing parameters'}, status=400)
        
    venue = get_object_or_404(Venue, pk=venue_id)
    try:
        slot_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)
        
    slots = get_venue_time_slots(venue, slot_date)
    return JsonResponse({
        'venue_name': venue.name,
        'venue_capacity': venue.capacity,
        'date': slot_date.strftime('%Y-%m-%d'),
        'formatted_date': slot_date.strftime('%A, %b %d, %Y'),
        'slots': slots
    })


def booking_create_view(request):
    initial_data = {}
    
    # Pre-fill query parameters from Calendar or Recommendation view
    if request.GET.get('venue'):
        initial_data['venue'] = request.GET.get('venue')
    if request.GET.get('date'):
        initial_data['date'] = request.GET.get('date')
    if request.GET.get('start_time'):
        initial_data['start_time'] = request.GET.get('start_time')
    if request.GET.get('end_time'):
        initial_data['end_time'] = request.GET.get('end_time')
    if request.GET.get('attendance'):
        initial_data['expected_attendance'] = request.GET.get('attendance')
        
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save()
            
            # Create in-app notification
            Notification.objects.create(
                title=f"New Booking Request #{booking.booking_ref}",
                message=f"Request submitted for '{booking.event_name}' at {booking.venue.name} on {booking.date}.",
                notification_type='INFO',
                booking=booking
            )
            
            messages.success(
                request,
                f"Booking request for '{booking.event_name}' submitted successfully! Reference ID: {booking.booking_ref}"
            )
            return redirect('booking_detail', booking_ref=booking.booking_ref)
        else:
            messages.error(request, "Form validation failed. Please check the errors below.")
    else:
        form = BookingForm(initial=initial_data)
        
    context = {
        'form': form,
        'equipment_list': Equipment.objects.all(),
        'venues': Venue.objects.filter(is_active=True),
    }
    return render(request, 'reservations/booking_form.html', context)


def my_bookings_view(request):
    status_filter = request.GET.get('status', 'ALL')
    search_query = request.GET.get('q', '')
    
    bookings = Booking.objects.all()
    
    if status_filter != 'ALL':
        bookings = bookings.filter(status=status_filter)
        
    if search_query:
        bookings = bookings.filter(
            Q(booking_ref__icontains=search_query) |
            Q(event_name__icontains=search_query) |
            Q(organizer_name__icontains=search_query) |
            Q(organizer_id__icontains=search_query) |
            Q(department_club__icontains=search_query)
        )
        
    context = {
        'bookings': bookings,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    return render(request, 'reservations/my_bookings.html', context)


def booking_detail_view(request, booking_ref):
    booking = get_object_or_404(Booking, booking_ref=booking_ref)
    context = {'booking': booking}
    return render(request, 'reservations/booking_detail.html', context)


def booking_cancel_view(request, booking_ref):
    booking = get_object_or_404(Booking, booking_ref=booking_ref)
    
    if request.method == 'POST':
        if booking.status in ['PENDING', 'APPROVED', 'RESERVED']:
            booking.status = 'CANCELLED'
            booking.save()
            
            Notification.objects.create(
                title=f"Booking Cancelled #{booking.booking_ref}",
                message=f"Booking for '{booking.event_name}' at {booking.venue.name} has been cancelled by organizer.",
                notification_type='WARNING',
                booking=booking
            )
            messages.warning(request, f"Booking {booking.booking_ref} has been cancelled.")
        else:
            messages.error(request, "This booking cannot be cancelled.")
            
        return redirect('booking_detail', booking_ref=booking.booking_ref)
        
    context = {'booking': booking}
    return render(request, 'reservations/booking_cancel_confirm.html', context)


def booking_print_view(request, booking_ref):
    booking = get_object_or_404(Booking, booking_ref=booking_ref)
    context = {'booking': booking}
    return render(request, 'reservations/booking_print.html', context)


def recommend_venue_view(request):
    results = None
    form = RecommendationRequestForm(request.GET or None)
    
    if form.is_valid():
        attendance = form.cleaned_data.get('expected_attendance')
        pref_date = form.cleaned_data.get('preferred_date')
        s_time = form.cleaned_data.get('start_time')
        e_time = form.cleaned_data.get('end_time')
        equipments = form.cleaned_data.get('required_equipment')
        
        equip_ids = [eq.id for eq in equipments] if equipments else []
        
        results = recommend_venues(
            attendance=attendance,
            required_equipment_ids=equip_ids,
            preferred_date=pref_date,
            start_time=s_time,
            end_time=e_time
        )
        
    context = {
        'form': form,
        'results': results,
    }
    return render(request, 'reservations/recommend.html', context)


def admin_dashboard_view(request):
    status_filter = request.GET.get('status', 'ALL')
    bookings = Booking.objects.all()
    
    if status_filter != 'ALL':
        bookings = bookings.filter(status=status_filter)
        
    venues = Venue.objects.annotate(total_bookings=Count('bookings'))
    
    context = {
        'bookings': bookings,
        'status_filter': status_filter,
        'venues': venues,
        'pending_count': Booking.objects.filter(status='PENDING').count(),
        'approved_count': Booking.objects.filter(status='APPROVED').count(),
        'reserved_count': Booking.objects.filter(status='RESERVED').count(),
        'rejected_count': Booking.objects.filter(status='REJECTED').count(),
        'cancelled_count': Booking.objects.filter(status='CANCELLED').count(),
    }
    return render(request, 'reservations/admin_dashboard.html', context)


@require_POST
def admin_booking_action_view(request, booking_ref):
    booking = get_object_or_404(Booking, booking_ref=booking_ref)
    action = request.POST.get('action')
    admin_notes = request.POST.get('admin_notes', '')
    
    if action == 'APPROVE':
        booking.status = 'APPROVED'
        msg = f"Booking {booking.booking_ref} approved successfully."
        ntype = 'SUCCESS'
    elif action == 'RESERVE':
        booking.status = 'RESERVED'
        msg = f"Booking {booking.booking_ref} confirmed and marked as Reserved."
        ntype = 'SUCCESS'
    elif action == 'REJECT':
        booking.status = 'REJECTED'
        msg = f"Booking {booking.booking_ref} rejected."
        ntype = 'DANGER'
    elif action == 'CANCEL':
        booking.status = 'CANCELLED'
        msg = f"Booking {booking.booking_ref} cancelled."
        ntype = 'WARNING'
    else:
        messages.error(request, "Invalid action.")
        return redirect('admin_dashboard')
        
    if admin_notes:
        booking.admin_notes = admin_notes
        
    booking.save()
    
    Notification.objects.create(
        title=f"Booking Status Updated: {booking.get_status_display()}",
        message=f"Booking #{booking.booking_ref} for '{booking.event_name}' status changed to {booking.get_status_display()}.",
        notification_type=ntype,
        booking=booking
    )
    
    messages.success(request, msg)
    return redirect('admin_dashboard')


@require_POST
def mark_notification_read_view(request, notification_id):
    notif = get_object_or_404(Notification, id=notification_id)
    notif.is_read = True
    notif.save()
    return JsonResponse({'status': 'ok'})
