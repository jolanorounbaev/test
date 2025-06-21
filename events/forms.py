from django import forms
from django.utils import timezone
from datetime import datetime
from .models import Event

class EventForm(forms.ModelForm):
    open_slots = forms.TypedChoiceField(
        choices=[(i, str(i)) for i in range(1, 21)],
        coerce=int,
        label='Open slots',
        initial=1
    )
    time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        required=True,
        label='Event Start Time',
        help_text='Pick the date and time when your event starts.'    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].widget.attrs['autocomplete'] = 'off'
        self.fields['description'].widget.attrs['autocomplete'] = 'off'
        # Set minimum datetime to current time (client-side validation)
        now = timezone.now()
        min_datetime = now.strftime('%Y-%m-%dT%H:%M')
        self.fields['time'].widget.attrs['min'] = min_datetime
    
    def clean_time(self):
        """Server-side validation to ensure event time is not in the past"""
        time = self.cleaned_data.get('time')
        if time:
            now = timezone.now()
            # Add a small buffer (1 minute) to account for form submission time
            from datetime import timedelta
            min_time = now + timedelta(minutes=1)
            
            if time < min_time:
                raise forms.ValidationError("Event start time must be at least 1 minute in the future.")
        return time
    
    class Meta:
        model = Event
        fields = [
            'title', 'image', 'description', 'address', 'open_slots', 'duration_minutes', 'visibility', 'time'
        ]
