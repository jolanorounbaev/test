from channels.generic.websocket import AsyncWebsocketConsumer
import json
from django.contrib.auth.models import AnonymousUser
from asgiref.sync import sync_to_async
from userprofile.models import Block
from django.db import models

async def is_user_blocked_async(current_user, other_user):
    """Check if users have blocked each other (async version)"""
    return await sync_to_async(Block.objects.filter(
        models.Q(blocker=current_user, blocked=other_user) | 
        models.Q(blocker=other_user, blocked=current_user)
    ).exists)()

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope["user"] and not isinstance(self.scope["user"], AnonymousUser):
            self.user = self.scope["user"]
            self.group_name = f"notifications_{self.user.id}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        # Not expecting to receive data from client
        pass

    async def send_notification(self, event):
        try:
            # Check if there's a sender_id and blocking status
            if 'sender_id' in event.get('content', {}):
                from registerandlogin.models import CustomUser
                current_user = self.user
                sender = await sync_to_async(CustomUser.objects.get)(id=event['content']['sender_id'])
                
                # Check if users have blocked each other
                is_blocked = await is_user_blocked_async(current_user, sender)
                
                if is_blocked:
                    print(f"[NotificationConsumer] Blocked notification from user {sender.id} to {current_user.id}")
                    return  # Don't send notification if blocked
            
            await self.send(text_data=json.dumps(event["content"]))
        except Exception as e:
            print(f"[NotificationConsumer] Error in send_notification: {str(e)}")
            # Still send the notification if there's an error (but log it)
            await self.send(text_data=json.dumps(event["content"]))
