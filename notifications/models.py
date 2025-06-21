from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.dispatch import receiver
from django.db.models.signals import post_save
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

User = get_user_model()

class FriendRequest(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_requests')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests')
    timestamp = models.DateTimeField(default=timezone.now)
    accepted = models.BooleanField(default=False)
    declined = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.from_user} ➝ {self.to_user}"

@receiver(post_save, sender=FriendRequest)
def notify_new_friend_request(sender, instance, created, **kwargs):
    if created and not instance.accepted and not instance.declined:
        # Check if users have blocked each other
        from userprofile.models import Block
        from django.db import models as django_models
        
        is_blocked = Block.objects.filter(
            django_models.Q(blocker=instance.from_user, blocked=instance.to_user) | 
            django_models.Q(blocker=instance.to_user, blocked=instance.from_user)
        ).exists()
        
        if is_blocked:
            return  # Don't send notification if users have blocked each other
            
        try:
            channel_layer = get_channel_layer()
            group_name = f"notifications_{instance.to_user.id}"
            
            # Send WebSocket notification
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "send_notification",
                    "content": {
                        "message": f"New friend request from {instance.from_user.first_name} {instance.from_user.last_name}",
                        "from_user": f"{instance.from_user.first_name} {instance.from_user.last_name}",
                        "notification_type": "friend_request",
                        "from_user_id": instance.from_user.id,
                        "request_id": instance.id,
                        "sender_id": instance.from_user.id  # Add sender_id for blocking check
                    }
                }
            )
            
        except Exception as e:
            pass  # Silently handle WebSocket errors
            
        # Also create a Notification object for persistence
        try:
            Notification.objects.create(
                user=instance.to_user,
                sender=instance.from_user,
                notification_type='friend_request',
                message=f"New friend request from {instance.from_user.first_name} {instance.from_user.last_name}",
                url=f"/notifications/"
            )
        except Exception as e:
            pass  # Silently handle database errors
            pass  # Silently handle database errors

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ("friend_request", "Friend Request"),        ("event_join_request", "Event Join Request"),
        ("message", "Message"),
        ("like", "Like"),
        ("comment", "Comment"),
        # Add more types as needed
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")  # Who receives the notification
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_notifications", null=True, blank=True)  # Who triggered it
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    message = models.TextField(blank=True)
    url = models.URLField(blank=True)  # Optional: link to the relevant page
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(default=timezone.now)
    link = models.CharField(max_length=255, blank=True, null=True)  # Add this line
    related_object_id = models.PositiveIntegerField(blank=True, null=True)  # To store join request ID or other related object IDs

    def __str__(self):
        return f"{self.notification_type} to {self.user} from {self.sender} at {self.timestamp}"

class Friendship(models.Model):
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friendship_user1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friendship_user2')
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user1', 'user2')

    def __str__(self):
        return f"{self.user1} & {self.user2}"

def get_friends(user):
    """Return a queryset of all friends for the given user."""
    user1_friends = Friendship.objects.filter(user1=user).values_list('user2', flat=True)
    user2_friends = Friendship.objects.filter(user2=user).values_list('user1', flat=True)
    friend_ids = list(user1_friends) + list(user2_friends)
    return User.objects.filter(id__in=friend_ids)
