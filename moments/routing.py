from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/moments/(?P<moment_id>[0-9a-f\-]+)/$', consumers.MomentConsumer.as_asgi()),
]
