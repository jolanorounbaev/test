import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError

class Moment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    content = models.TextField(max_length=500)
    
    flag_count = models.PositiveIntegerField(default=0)
    fire_count = models.PositiveIntegerField(default=0)
    heart_count = models.PositiveIntegerField(default=0)


    image = models.ImageField(
        upload_to='moments/',
        blank=True,
        null=True,
        help_text="Optional image"
    )
    video = models.FileField(
        upload_to='moments/',
        blank=True,
        null=True,
        help_text="Optional video (MP4 recommended)"
    )
    youtube_link = models.URLField(
        blank=True,
        null=True,
        help_text="Optional YouTube link"
    )

    # 🔥 Tag filtering for visibility
    interests = models.JSONField(
        help_text="List of interest tags, e.g. ['Drawing', 'Chess']"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    # 💬 Chat / activity features
    activity_count = models.IntegerField(default=0)
    last_active = models.DateTimeField(default=timezone.now)

    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='joined_moments',
        blank=True
    )
    max_participants = models.PositiveIntegerField(default=10)

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=20)
        super().save(*args, **kwargs)

    def extend_expiry(self, minutes=10):
        self.expires_at += timedelta(minutes=minutes)
        self.save()

    def is_full(self):
        return self.participants.count() >= self.max_participants

    def is_expired(self):
        return timezone.now() > self.expires_at

    def clean(self):
        if self.image and self.video:
            raise ValidationError("You can upload either an image or a video, not both.")
        
    @property
    def remaining_time(self):
       remaining = self.expires_at - timezone.now()
       total_seconds = int(remaining.total_seconds())

       if total_seconds <= 0:
        return "expired"
       elif total_seconds < 60:
        return f"{total_seconds}s"
       elif total_seconds < 3600:
        return f"{total_seconds // 60}m"
       else:
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours}h {minutes}m"
   

    def __str__(self):
        return f"{self.user.email} @ {self.created_at.strftime('%H:%M')}"

    @property
    def is_hot(self):
       return self.fire_count >= 25


class MomentPing(models.Model):
    moment = models.ForeignKey('Moment', on_delete=models.CASCADE, related_name='pings')
    from_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_pings')
    to_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_pings')
    timestamp = models.DateTimeField(auto_now_add=True)
    seen = models.BooleanField(default=False)

    class Meta:
        unique_together = ('moment', 'from_user', 'to_user')


class MomentComment(models.Model):
    moment = models.ForeignKey(Moment, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} on {self.moment}"
    
    def get_gif_url(self):
        """Extract GIF URL from content if it contains one"""
        import re
        gif_pattern = r'https?://[^\s]+\.gif'
        match = re.search(gif_pattern, self.content)
        return match.group(0) if match else None
    
    def get_content_without_gif(self):
        """Get content with GIF URLs removed"""
        import re
        gif_pattern = r'https?://[^\s]+\.gif'
        return re.sub(gif_pattern, '', self.content).strip()

class MomentReply(models.Model):
    comment = models.ForeignKey(MomentComment, on_delete=models.CASCADE, related_name='replies')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} replied to comment {self.comment.id}"




# Below your Moment model

class FireReaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    moment = models.ForeignKey(Moment, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'moment')

    def __str__(self):
        return f"{self.user} 🔥 {self.moment}"


class HeartReaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    moment = models.ForeignKey(Moment, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'moment')

    def __str__(self):
        return f"{self.user} ❤️ {self.moment}"


# models.py
class MomentFlag(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    moment = models.ForeignKey(Moment, on_delete=models.CASCADE, related_name='flags')
    flagged_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'moment')  # One flag per user per moment

# Add this field to Moment:
flag_count = models.PositiveIntegerField(default=0)


class FlaggedMoment(Moment):
    class Meta:
        proxy = True
        verbose_name = "Flagged Moment"
        verbose_name_plural = "Flagged Moments"
