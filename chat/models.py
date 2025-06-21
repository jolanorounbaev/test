from django.db import models
from django.conf import settings

class ChatRoom(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    is_group = models.BooleanField(default=False)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='chatrooms')
    last_message = models.ForeignKey(
    'Message',
    null=True,
    blank=True,
    on_delete=models.SET_NULL,
    related_name='+'
)
    def __str__(self):
        return self.name if self.name else ", ".join([user.full_name for user in self.participants.all()])

class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False) 
    image = models.ImageField(upload_to='chat_images/', blank=True, null=True)
    video = models.FileField(upload_to='chat_videos/', blank=True, null=True)
    reply_to = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')

    def __str__(self):
        return self.content[:50]  # Only show the message text, up to 50 chars
