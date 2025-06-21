import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import Message, ChatRoom
from notifications.models import Notification
from userprofile.models import Block
from django.db import models
from datetime import datetime

async def is_user_blocked_async(current_user, other_user):
    """Check if users have blocked each other (async version)"""
    return await sync_to_async(Block.objects.filter(
        models.Q(blocker=current_user, blocked=other_user) | 
        models.Q(blocker=other_user, blocked=current_user)
    ).exists)()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        
        if self.scope['user'] == AnonymousUser():
            await self.close(code=4001)
            return
            
        self.room_group_name = f'chat_{self.room_id}'
        
        try:
            # Verify room exists and user is participant
            room = await sync_to_async(ChatRoom.objects.get)(id=self.room_id)
            if not await sync_to_async(room.participants.filter(id=self.scope['user'].id).exists)():
                await self.close(code=4003)
                return
                
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()
            print(f"✅ WebSocket connected for room {self.room_id}")
            
        except ChatRoom.DoesNotExist:
            await self.close(code=4004)
        except Exception as e:
            print(f"Connection error: {str(e)}")
            await self.close(code=4000)

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        print(f"⚠️ Disconnected from room {self.room_id}, code: {close_code}")

    async def receive(self, text_data):
        print(f"[ChatConsumer] receive called with text_data: {text_data}")  # DEBUG
        try:
            data = json.loads(text_data)
            message = data.get('message', '').strip()
            reply_to_id = data.get('reply_to')  # Get reply_to from the data
            
            if not message:
                print("[ChatConsumer] No message to send.")  # DEBUG
                return
                
            # Save message to DB first
            saved_message = await save_message(self.room_id, self.scope['user'], message, reply_to_id)
            
            if not saved_message:
                print("[ChatConsumer] Failed to save message.")  # DEBUG
                raise Exception("Failed to save message")
            
            # Prepare reply data if this is a reply
            reply_data = {}
            if reply_to_id:
                reply_data = await get_reply_data(saved_message)
                print(f"[DEBUG] Reply data: {reply_data}")  # Add debug output
            
            # Broadcast to group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender_id': self.scope['user'].id,
                    'timestamp': saved_message.timestamp.isoformat(),
                    'username': self.scope["user"].full_name,
                    'message_id': saved_message.id,  # Include message ID
                    'sender_profile_picture': self.scope['user'].profile_picture.url if self.scope['user'].profile_picture else None,
                    **reply_data  # Include reply data if present
                }
            )
            # Send chat notification to all other participants (user-specific group)
            from channels.layers import get_channel_layer
            channel_layer = get_channel_layer()
            from .models import ChatRoom
            room = await sync_to_async(ChatRoom.objects.get)(id=self.room_id)
            for participant in await sync_to_async(list)(room.participants.all()):
                if participant.id != self.scope['user'].id:
                    print(f"[ChatConsumer] Sending chat_notify to {participant.id} with message: {message}")  # DEBUG
                    chat_notify_group = f"chat_notify_{participant.id}"
                    await channel_layer.group_send(
                        chat_notify_group,
                        {
                            "type": "chat_notify",
                            "content": {
                                "type": "chat_message",
                                "message": message,
                                "sender_id": self.scope['user'].id,
                                "timestamp": saved_message.timestamp.isoformat(),
                                "username": self.scope["user"].full_name,
                                "room_id": self.room_id,
                                "message_id": saved_message.id
                            }
                        }
                    )
            print(f"[ChatConsumer] Finished sending chat_notify for message: {message}")  # DEBUG
        except Exception as e:
            print(f"Error processing message: {str(e)}")
            await self.send(text_data=json.dumps({
                'error': str(e),
                'type': 'error'
            }))

    async def chat_message(self, event):
        try:
            from registerandlogin.models import CustomUser
            
            # Get sender object
            sender = await sync_to_async(CustomUser.objects.get)(id=event['sender_id'])
            
            # Check if current user has blocked the sender or vice versa
            is_blocked = await is_user_blocked_async(self.scope['user'], sender)
            
            # Include all reply data if present
            message_data = {
                'type': 'chat_message',
                'message': event['message'],
                'sender_id': event['sender_id'],
                'timestamp': event['timestamp'],
                'username': event['username'],
                'message_id': event['message_id'],
                'sender_profile_picture': event.get('sender_profile_picture'),
                'is_blocked': is_blocked  # Add blocking info
            }
            
            # Add reply data if present
            if 'reply_to_message' in event:
                message_data.update({
                    'reply_to_message': event['reply_to_message'],
                    'reply_to_user': event['reply_to_user'],
                    'reply_to_id': event['reply_to_id']
                })
                print(f"[DEBUG] Sending reply data to client: {message_data.get('reply_to_user', 'None')}")
            
            await self.send(text_data=json.dumps(message_data))
            # Create a Notification for the recipient (if not sender)
            if self.scope['user'].id != event['sender_id']:
                # Only create notification for direct (non-group) chat
                from .models import ChatRoom
                room = await sync_to_async(ChatRoom.objects.get)(id=self.room_id)
                # For direct chat, find the other participant
                if not room.is_group:
                    for participant in await sync_to_async(list)(room.participants.all()):
                        if participant.id != event['sender_id']:
                            await sync_to_async(Notification.objects.create)(
                                user=participant,
                                sender_id=event['sender_id'],
                                notification_type='message',
                                message=event['message'],
                                room_id=self.room_id,
                                is_read=False
                            )
                            # WebSocket notification to the browser
                            user_channel_group = f"user_{participant.id}"
                            await self.channel_layer.group_send(
                                user_channel_group,
                                {
                                    "type": "notify_browser",
                                    "payload": {
                                        "notification_id": await sync_to_async(lambda: Notification.objects.filter(user=participant).last().id)(),
                                        "type": "message",
                                        "title": "New message",
                                        "message": f"New message from {event['username']}",
                                        "from_user": event['username'],
                                        "timestamp": event['timestamp'],
                                        "room_id": self.room_id,
                                        "is_read": False
                                    }
                                }
                            )
                            # Send the notification to desktop/mobile
                            send_notification_group = f"send_notification_{participant.id}"
                            await self.channel_layer.group_send(
                                send_notification_group,
                                {
                                    "type": "send_desktop_notification",
                                    "payload": {
                                        "title": "ProximityLinked",
                                        "message": event['message'],
                                        "icon_url": "http://127.0.0.1:8000/static/img/appicon.png", # Adjust URL as needed
                                        "click_url": f"http://127.0.0.1:8000/chat/{self.room_id}/",
                                        "user_id": participant.id
                                    }
                                }
                            )
        except Exception as e:
            print(f"Error in chat_message: {str(e)}")

# Helper functions
@sync_to_async
def save_message(room_id, user, content, reply_to_id=None):
    try:
        room = ChatRoom.objects.get(id=room_id)
        reply_to_message = None
        if reply_to_id:
            try:
                reply_to_message = Message.objects.get(id=reply_to_id, room=room)
            except Message.DoesNotExist:
                pass  # Ignore invalid reply_to_id
        
        message = Message.objects.create(
            room=room,
            sender=user,
            content=content,
            reply_to=reply_to_message
        )
        return message
    except Exception as e:
        print(f"Error saving message: {str(e)}")
        return None

@sync_to_async
def get_reply_data(message):
    """Get reply data for a message if it's a reply"""
    if message.reply_to:
        return {
            'reply_to_message': message.reply_to.content,
            'reply_to_user': message.reply_to.sender.full_name or message.reply_to.sender.username,
            'reply_to_id': message.reply_to.id
        }
    return {}
