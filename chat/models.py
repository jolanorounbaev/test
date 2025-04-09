from django.db import models
from django.conf import settings
from django.utils import timezone

class GroupChat(models.Model):
    name = models.CharField(max_length=100)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_chats'
    )
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name


class GroupMember(models.Model):
    group = models.ForeignKey(GroupChat, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('group', 'user')


class ChatMessage(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    # One of these will be set
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='received_messages'
    )
    group = models.ForeignKey(
        GroupChat,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='chat_messages'
    )

    def is_private(self):
        return self.receiver is not None

    def __str__(self):
        if self.group:
            return f"[Group:{self.group.name}] {self.sender} > {self.content[:20]}"
        elif self.receiver:
            return f"[Private] {self.sender} to {self.receiver}: {self.content[:20]}"
        return f"{self.sender}: {self.content[:20]}"
