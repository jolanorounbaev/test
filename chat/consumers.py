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
        if hasattr(self, 'room_group_name'):            await self.channel_layer.group_discard(
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
                    # Check if the participant has blocked the sender or vice versa
                    is_blocked = await is_user_blocked_async(self.scope['user'], participant)
                    if not is_blocked:  # Only send notification if not blocked
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
                    'reply_to_id': event['reply_to_id']                })
                print(f"[DEBUG] Sending reply data to client: {message_data.get('reply_to_user', 'None')}")
            
            await self.send(text_data=json.dumps(message_data))
            
            # Create a Notification for the recipient (if not sender and not blocked)
            if self.scope['user'].id != event['sender_id'] and not is_blocked:
                # Only create notification for direct (non-group) chat
                from .models import ChatRoom
                room = await sync_to_async(ChatRoom.objects.get)(id=self.room_id)
                # For direct chat, find the other participant
                if not room.is_group:
                    for participant in await sync_to_async(list)(room.participants.all()):
                        if participant.id != event['sender_id']:
                            # Double-check blocking status for this specific participant
                            participant_blocked = await is_user_blocked_async(sender, participant)
                            if not participant_blocked:
                                await sync_to_async(Notification.objects.create)(
                                    user=participant,
                                    sender_id=event['sender_id'],
                                    notification_type='message',
                                    message=event['message'],
                                    url=f"/chat/{self.room_id}/"
                                )
                                # Send real-time notification to recipient's notification group
                                from channels.layers import get_channel_layer
                                channel_layer = get_channel_layer()
                                group_name = f"notifications_{participant.id}"
                                await channel_layer.group_send(
                                    group_name,
                                    {
                                        "type": "send_notification",
                                        "content": {
                                            "message": f"New message from {event['username']}",
                                            "from_user": event['username'],
                                            "url": f"/chat/{self.room_id}/",
                                            "notification_type": "message"
                                        }
                                    }
                                )
                                # Send real-time notification to recipient's chat_notify group (for global chat notifications)
                                chat_notify_group = f"chat_notify_{participant.id}"
                                await channel_layer.group_send(
                                    chat_notify_group,
                                    {
                                        "type": "chat_notify",
                                        "content": {
                                            "type": "chat_message",
                                            "message": event['message'],
                                            "sender_id": event['sender_id'],
                                            "timestamp": event['timestamp'],
                                            "username": event['username'],
                                            "room_id": self.room_id,
                                            "message_id": event['message_id']
                                        }
                                    }
                                )
        except Exception as e:
            print(f"Error sending message: {str(e)}")


@sync_to_async
def save_message(room_id, sender, content, reply_to_id=None):
    print(f"[save_message] Starting for room_id={room_id}, sender={sender}, content={content}, reply_to_id={reply_to_id}")
    try:
        room = ChatRoom.objects.get(id=room_id)
        print(f"[save_message] Found room: {room}")
        
        # Get the reply_to message if provided
        reply_to_message = None
        if reply_to_id:
            try:
                reply_to_message = Message.objects.get(id=reply_to_id, room=room)
                print(f"[save_message] Found reply_to message: {reply_to_message}")
            except Message.DoesNotExist:
                print(f"[save_message] Reply message not found: {reply_to_id}")
        
        message = Message.objects.create(
            room=room, 
            sender=sender, 
            content=content,
            reply_to=reply_to_message
        )
        room.last_message = message
        room.save(update_fields=["last_message"])
        print(f"[save_message] Message saved: {message}")
        return message
    except ChatRoom.DoesNotExist:
        print(f"[save_message] Room does not exist: {room_id}")
    except Exception as e:
        print(f"[save_message] Unexpected error: {e}")
    return None

@sync_to_async
def get_reply_data(message):
    """Safely get reply data for a message"""
    if message.reply_to:
        return {
            'reply_to_message': message.reply_to.content,
            'reply_to_user': message.reply_to.sender.full_name,
            'reply_to_id': message.reply_to.id
        }
    return {}
