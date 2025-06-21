"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing other modules that use Django models
django_asgi_app = get_asgi_application()

# Now import the routing modules
try:
    import chat.routing
    chat_patterns = chat.routing.websocket_urlpatterns
except ImportError:
    chat_patterns = []

try:
    import notifications.routing
    notification_patterns = notifications.routing.websocket_urlpatterns
except ImportError:
    notification_patterns = []

try:
    import events.routing
    event_patterns = events.routing.websocket_urlpatterns
except ImportError:
    event_patterns = []

try:
    import moments.routing
    moment_patterns = moments.routing.websocket_urlpatterns
except ImportError:
    moment_patterns = []

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            chat_patterns +
            notification_patterns +
            event_patterns +
            moment_patterns
        )
    ),
})
