import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser

class EventConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Basic event consumer - can be expanded later
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        # Handle incoming WebSocket messages
        pass
