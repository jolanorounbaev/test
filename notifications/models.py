from django.db import models
from django.conf import settings
from django.utils import timezone

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('friend_request', 'Friend Request'),
        ('message', 'Message'),
        ('other', 'Other'),
    ]

    to_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    from_user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(default=timezone.now)

    @classmethod
    def create_friend_request_notification(cls, from_user, to_user):
        return cls.objects.create(
            to_user=to_user,
            from_user=from_user,
            type='friend_request',
            message=f"{from_user.full_name} sent you a friend request",
            link=f"/friends/requests/"
        )
    
    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.type} → {self.to_user.email} at {self.timestamp}"


class Friendship(models.Model):
    user1 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='friends')
    user2 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ('user1', 'user2')
        verbose_name_plural = 'friendships'
    
    def __str__(self):
        return f"{self.user1} and {self.user2} are friends"
    

class FriendRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    
    from_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_requests')
    to_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_requests')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ('from_user', 'to_user')
    
    def __str__(self):
        return f"{self.from_user} → {self.to_user} ({self.status})"
    
    def accept(self):
        self.status = 'accepted'
        self.save()
        # Create friendship both ways
        Friendship.objects.get_or_create(user1=self.from_user, user2=self.to_user)
        Friendship.objects.get_or_create(user1=self.to_user, user2=self.from_user)
        # Create notification
        Notification.objects.create(
            to_user=self.from_user,
            from_user=self.to_user,
            type='friend_request',
            message=f"{self.to_user.full_name} accepted your friend request",
            link=f"/profile/{self.to_user.id}/"
        )
    
    def reject(self):
        self.status = 'rejected'
        self.save()
        # Create notification
        Notification.objects.create(
            to_user=self.from_user,
            from_user=self.to_user,
            type='friend_request',
            message=f"{self.to_user.full_name} declined your friend request",
            link=f"/profile/{self.to_user.id}/"
        )
