# chat/routing.py
from django.urls import re_path

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter, ChannelNameRouter
from channels.security.websocket import AllowedHostsOriginValidator

from django.core.asgi import get_asgi_application
# from . import consumers
from .consumers import TaskConsumer, CHANNEL_NAME_TASK_RESULT, ChatConsumer


# This as_asgi() works like Django's as_view()
# https://channels.readthedocs.io/en/stable/tutorial/part_2.html
websocket_urlpatterns = [
    re_path(r"ws/powerscan/chat/(?P<room_name>\w+)/$", ChatConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(URLRouter(websocket_urlpatterns))),
    "channel": ChannelNameRouter({
        CHANNEL_NAME_TASK_RESULT : TaskConsumer.as_asgi(),
        }),
    })
