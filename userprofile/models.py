# models.py

from django.db import models
from django.conf import settings
from registerandlogin.models import CustomUser
from django.utils import timezone

class ContentItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='content_items')
    title = models.CharField(max_length=100)
    description = models.TextField(max_length=300, blank=True)  # roughly 50 words
    image = models.ImageField(upload_to='content_images/', blank=True, null=True)
    youtube_url = models.URLField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.title}"

    def get_youtube_embed_url(self):
        if self.youtube_url and 'youtube.com' in self.youtube_url:
            try:
                video_id = self.youtube_url.split('v=')[1].split('&')[0]
                return f"https://www.youtube.com/embed/{video_id}"
            except IndexError:
                return None
        return None
    
class VisitedPlace(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="visited_places")
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='visited_places/')

class Achievement(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="achievements")
    title = models.CharField(max_length=100)
    icon = models.ImageField(upload_to='achievements/', blank=True, null=True)

class Quote(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="quotes")
    text = models.TextField(max_length=300)

class Block(models.Model):
    """Model to handle user blocking functionality"""
    blocker = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='blocks_made',
        help_text="The user who is doing the blocking"
    )
    blocked = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='blocks_received',
        help_text="The user who is being blocked"
    )
    created_at = models.DateTimeField(default=timezone.now)
    reason = models.CharField(
        max_length=200, 
        blank=True, 
        help_text="Optional reason for blocking"
    )

    class Meta:
        unique_together = ('blocker', 'blocked')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.blocker.full_name} blocked {self.blocked.full_name}"

    @staticmethod
    def is_blocked(user1, user2):
        """Check if user1 has blocked user2 OR user2 has blocked user1"""
        return Block.objects.filter(
            models.Q(blocker=user1, blocked=user2) | 
            models.Q(blocker=user2, blocked=user1)
        ).exists()

    @staticmethod
    def get_blocked_users(user):
        """Get all users that this user has blocked"""
        return CustomUser.objects.filter(blocks_received__blocker=user)

    @staticmethod
    def get_users_who_blocked(user):
        """Get all users who have blocked this user"""
        return CustomUser.objects.filter(blocks_made__blocked=user)
