from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.conf import settings
from .models import ChatRoom

@receiver(post_delete, sender=settings.AUTH_USER_MODEL)
def cleanup_chat_rooms_on_user_delete(sender, instance, **kwargs):
    """
    When a user is deleted, clean up their chat rooms.
    For one-on-one chats, delete the entire room.
    For group chats, just remove the user from participants.
    """
    # Get all chat rooms where this user was a participant
    user_rooms = ChatRoom.objects.filter(participants=instance)
    
    for room in user_rooms:
        if not room.is_group:
            # For one-on-one chats, delete the entire room
            # since it doesn't make sense to keep it with only one participant
            room.delete()
        else:
            # For group chats, just remove the user from participants
            # The room can continue to exist with remaining participants
            room.participants.remove(instance)
            
            # If the group chat now has only one participant, delete it
            if room.participants.count() <= 1:
                room.delete()
