import re
from datetime import date
from django import forms
from django.core.exceptions import ValidationError
from .models import Booking, Venue, Equipment
from .utils import check_booking_conflict


class BookingForm(forms.ModelForm):
    required_equipment = forms.ModelMultipleChoiceField(
        queryset=Equipment.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'equipment-checkbox-grid'}),
        required=False,
        label="Required AV Equipment / Infrastructure"
    )

    class Meta:
        model = Booking
        fields = [
            'venue', 'event_name', 'event_type', 'event_description',
            'organizer_name', 'organizer_id', 'email', 'phone', 'department_club',
            'date', 'start_time', 'end_time', 'expected_attendance',
            'required_equipment', 'special_requirements',
        ]
        widgets = {
            'venue': forms.Select(attrs={'class': 'form-select', 'id': 'id_venue'}),
            'event_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Annual Techfest 2026 – Innovision'
            }),
            'event_type': forms.Select(attrs={'class': 'form-select'}),
            'event_description': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'Brief agenda, speakers, and event flow...'
            }),
            'organizer_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Dr. Ramesh Bajaj / Student President Name'
            }),
            'organizer_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. FAC-LPU-4410 or UID-11014223'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'yourname@lpu.co.in'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+91 98765 43210'
            }),
            'department_club': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. School of CSE / Lovely Cultural Club / NSS'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date', 'id': 'id_date'
            }),
            'start_time': forms.TimeInput(attrs={
                'class': 'form-control', 'type': 'time', 'id': 'id_start_time'
            }),
            'end_time': forms.TimeInput(attrs={
                'class': 'form-control', 'type': 'time', 'id': 'id_end_time'
            }),
            'expected_attendance': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': 'e.g. 500', 'id': 'id_attendance'
            }),
            'special_requirements': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2,
                'placeholder': 'e.g. VIP seating arrangement, tent setup, generator, press access...'
            }),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '')
        clean_p = re.sub(r'[\s\-\+\(\)]', '', phone)
        if len(clean_p) < 8 or not clean_p.isdigit():
            raise ValidationError(
                "Enter a valid phone number (at least 8 digits)."
            )
        return phone

    def clean_date(self):
        booking_date = self.cleaned_data.get('date')
        if booking_date and booking_date < date.today():
            raise ValidationError(
                "Reservation date cannot be in the past. Please select today or a future date."
            )
        return booking_date

    def clean(self):
        cleaned_data   = super().clean()
        venue          = cleaned_data.get('venue')
        booking_date   = cleaned_data.get('date')
        start_time     = cleaned_data.get('start_time')
        end_time       = cleaned_data.get('end_time')
        attendance     = cleaned_data.get('expected_attendance')

        # Time order
        if start_time and end_time and end_time <= start_time:
            self.add_error('end_time', "End time must be after the start time.")

        # Capacity check
        if venue and attendance:
            if attendance > venue.capacity:
                self.add_error(
                    'expected_attendance',
                    f"Expected attendance ({attendance}) exceeds the approximate capacity "
                    f"of {venue.name} (~{venue.capacity} persons)."
                )

        # Conflict / double-booking check
        if venue and booking_date and start_time and end_time and (end_time > start_time if (start_time and end_time) else False):
            exclude_id = self.instance.pk if self.instance and self.instance.pk else None
            has_conflict, conflicts = check_booking_conflict(
                venue, booking_date, start_time, end_time,
                exclude_booking_id=exclude_id
            )
            if has_conflict:
                c = conflicts[0]
                raise ValidationError(
                    f"Scheduling Conflict! {venue.name} is already "
                    f"{'reserved' if c.status == 'RESERVED' else 'pending'} for "
                    f"'{c.event_name}' from {c.start_time.strftime('%I:%M %p')} "
                    f"to {c.end_time.strftime('%I:%M %p')} on "
                    f"{booking_date.strftime('%d %b %Y')}. "
                    f"Please choose a different time slot or venue."
                )

        return cleaned_data


class VenueFilterForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name, location... e.g. SDMA, Uni Polis'
        })
    )
    venue_type = forms.ChoiceField(
        required=False,
        choices=[('', 'All Types')] + list(Venue.VENUE_TYPE_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    min_capacity = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Min Seats'})
    )
    is_outdoor = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    has_ac = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    has_stage = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    has_tent_setup = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    has_video_conferencing = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class RecommendationRequestForm(forms.Form):
    expected_attendance = forms.IntegerField(
        required=True, min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control', 'placeholder': 'e.g. 2500'
        })
    )
    preferred_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    start_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    end_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    required_equipment = forms.ModelMultipleChoiceField(
        queryset=Equipment.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'equipment-checkbox-grid'}),
        required=False
    )
