import json
from channels.generic.websocket import AsyncWebsocketConsumer
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

class ChatNotifyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        user = self.scope["user"]
        print(f"[ChatNotifyConsumer] connect: user_id={self.user_id}, user={user}")  # DEBUG
        if not user.is_authenticated or str(user.id) != str(self.user_id):
            print(f"[ChatNotifyConsumer] REFUSED: user_id={self.user_id}, user={user}")  # DEBUG
            await self.close(code=4001)
            return
        self.group_name = f"chat_notify_{self.user_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        print(f"[ChatNotifyConsumer] ACCEPTED: group={self.group_name}")  # DEBUG

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        print(f"[ChatNotifyConsumer] disconnect: group={getattr(self, 'group_name', None)}, code={close_code}")  # DEBUG

    async def receive(self, text_data):
        print(f"[ChatNotifyConsumer] receive called (should not happen)")  # DEBUG
        pass

    async def chat_notify(self, event):
        try:
            print(f"[ChatNotifyConsumer] chat_notify: {event['content']}")  # DEBUG
            
            # Check if the sender is blocked before sending the notification
            if 'sender_id' in event['content']:
                from registerandlogin.models import CustomUser
                current_user = self.scope['user']
                sender = await sync_to_async(CustomUser.objects.get)(id=event['content']['sender_id'])
                
                # Check if users have blocked each other
                is_blocked = await is_user_blocked_async(current_user, sender)
                
                if is_blocked:
                    print(f"[ChatNotifyConsumer] Blocked notification from user {sender.id} to {current_user.id}")
                    return  # Don't send notification if blocked
            
            await self.send(text_data=json.dumps(event["content"]))
        except Exception as e:
            print(f"[ChatNotifyConsumer] Error in chat_notify: {str(e)}")  # DEBUG
