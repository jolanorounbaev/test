from django.db import models
from django.conf import settings

# Create your models here.

class Event(models.Model):
    VISIBILITY_CHOICES = [
        ('public', 'Public'),        ('friends', 'Friends'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('full', 'Full'),
        ('expired', 'Expired'),
    ]
    DURATION_CHOICES = [
        (5, '5 minutes'),
        (10, '10 minutes'),
        (20, '20 minutes'),
        (30, '30 minutes'),
        (60, '1 hour'),
        (120, '2 hours'),
    ]
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='content_images/', blank=True, null=True)
    description = models.TextField()
    address = models.CharField(max_length=255)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    open_slots = models.PositiveIntegerField()
    time = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(choices=DURATION_CHOICES, default=60, help_text="Event duration in minutes")
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='public')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='events_created')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    def get_end_time(self):
        """Calculate the end time of the event based on start time and duration"""
        if self.time and self.duration_minutes:
            from datetime import timedelta
            return self.time + timedelta(minutes=self.duration_minutes)
        return None

    def is_active(self):
        """Check if the event is currently active (between start and end time)"""
        from django.utils import timezone
        now = timezone.now()
        if self.time and self.get_end_time():
            return self.time <= now <= self.get_end_time()
        return False

    def get_time_remaining(self):
        """Get remaining time in minutes, returns None if event hasn't started or has ended"""
        from django.utils import timezone
        now = timezone.now()
        end_time = self.get_end_time()
        
        if not end_time:
            return None
        
        if now > end_time:
            return 0  # Event has ended
        
        if now < self.time:
            return None  # Event hasn't started yet
        
        remaining = end_time - now
        return int(remaining.total_seconds() / 60)

    def is_full(self):
        """Check if the event has no open slots remaining"""
        return self.open_slots == 0

    def update_status_if_full(self):
        """Update status to 'full' if no slots remaining"""
        if self.is_full() and self.status == 'active':
            self.status = 'full'
            self.save()

    def update_status_if_not_full(self):
        """Update status back to 'active' if slots become available and event hasn't expired"""
        if not self.is_full() and self.status == 'full':
            # Only change back to active if the event hasn't actually expired time-wise
            from django.utils import timezone
            now = timezone.now()
            end_time = self.get_end_time()
            if end_time and now <= end_time:
                self.status = 'active'
                self.save()

    def __str__(self):
        return self.title

class EventJoinRequest(models.Model):
    STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='join_requests')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='requested')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'event')

    def __str__(self):
        return f"{self.user} requests to join {self.event} ({self.status})"
