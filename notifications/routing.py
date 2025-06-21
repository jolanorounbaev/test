from django.urls import re_path
from . import consumers

# Notifications WebSocket URL patterns
websocket_urlpatterns = [
    re_path(r'ws/notifications/(?P<user_id>\w+)/$', consumers.NotificationConsumer.as_asgi()),
]
