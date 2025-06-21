"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
import django  # ✅ Must be before importing anything Django-related

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()  # ✅ Important: initialize Django settings before imports

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import chat.routing  # This depends on Django models/settings being loaded
import notifications.routing
import events.routing
import moments.routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            chat.routing.websocket_urlpatterns +
            notifications.routing.websocket_urlpatterns +
            events.routing.websocket_urlpatterns +
            moments.routing.websocket_urlpatterns
        )
    ),
})
