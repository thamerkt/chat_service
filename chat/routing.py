from django.urls import re_path
from . import consumers

import re

UUID_PATTERN = (
    r'[0-9a-fA-F]{8}-'
    r'[0-9a-fA-F]{4}-'
    r'[0-9a-fA-F]{4}-'
    r'[0-9a-fA-F]{4}-'
    r'[0-9a-fA-F]{12}'
)

USER_ID_PATTERN = rf'(?:{UUID_PATTERN}|\d+)'  # Accepts either UUID or numeric IDs

websocket_urlpatterns = [
    re_path(
        rf'^ws/chatroom/(?P<room_id>[\w\-]+(?:_[\w\-]+)*)/(?P<user_id>{USER_ID_PATTERN})/$',
        consumers.ChatConsumer.as_asgi()
    ),
    re_path(
        rf'^ws/notifications/(?P<user_id>{UUID_PATTERN})/$',
        consumers.NotificationConsumer.as_asgi()
    ),
]
