# models.py

from django.db import models
from django.conf import settings

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
    
