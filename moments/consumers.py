import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils.timezone import now
from channels.db import database_sync_to_async
from .models import Moment


class MomentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.moment_id = self.scope['url_route']['kwargs']['moment_id']
        self.room_group_name = f'moment_{self.moment_id}'
        self.user = self.scope["user"]

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        # Notify group that user joined
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'user': self.user.get_full_name() or self.user.email,
            }
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

        # Notify group that user left
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_left',
                'user': self.user.get_full_name() or self.user.email,
            }
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        user_display = self.user.get_full_name() or self.user.email

        if 'message' in data:
            message = data['message']
            response = {
                'type': 'reply',
                'user': user_display,
                'message': message,
                'timestamp': now().isoformat(),
            }
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'broadcast_reply',
                    'reply': response
                }
            )

        elif 'reaction' in data:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'broadcast_reaction',
                    'reaction': {
                        'type': data['reaction'],
                        'user': user_display,
                        'moment_id': self.moment_id,
                        'timestamp': now().isoformat(),
                    }
                }
            )
            
    @database_sync_to_async
    def mark_activity(self):
      try:
        moment = Moment.objects.get(id=self.moment_id)
        moment.activity_count += 1
        moment.last_active = now()
        moment.save()
      except Moment.DoesNotExist:
        pass         

    # Broadcast message reply
    async def broadcast_reply(self, event):
        await self.send(text_data=json.dumps(event['reply']))

    # Broadcast reaction (e.g. 🔥 👏)
    async def broadcast_reaction(self, event):
        await self.send(text_data=json.dumps({'reaction': event['reaction']}))

    # Presence: someone joined
    async def user_joined(self, event):
        await self.send(text_data=json.dumps({'join': event['user']}))

    # Presence: someone left
    async def user_left(self, event):
        await self.send(text_data=json.dumps({'leave': event['user']}))
