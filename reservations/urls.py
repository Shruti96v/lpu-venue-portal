from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    
    # Venues
    path('venues/', views.venue_list_view, name='venue_list'),
    path('venues/compare/', views.venue_compare_view, name='venue_compare'),
    path('venues/<slug:slug>/', views.venue_detail_view, name='venue_detail'),
    
    # Availability Calendar & API
    path('calendar/', views.calendar_view, name='calendar'),
    path('api/venue-slots/', views.api_venue_slots, name='api_venue_slots'),
    
    # Booking
    path('booking/new/', views.booking_create_view, name='booking_create'),
    path('my-bookings/', views.my_bookings_view, name='my_bookings'),
    path('booking/<str:booking_ref>/', views.booking_detail_view, name='booking_detail'),
    path('booking/<str:booking_ref>/cancel/', views.booking_cancel_view, name='booking_cancel'),
    path('booking/<str:booking_ref>/print/', views.booking_print_view, name='booking_print'),
    
    # Smart Recommendation Engine
    path('recommend/', views.recommend_venue_view, name='recommend_venue'),
    
    # Custom Admin Management Dashboard
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin-dashboard/action/<str:booking_ref>/', views.admin_booking_action_view, name='admin_booking_action'),
    path('notification/<int:notification_id>/read/', views.mark_notification_read_view, name='mark_notification_read'),
]
