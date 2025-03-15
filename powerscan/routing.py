# chat/routing.py
from django.urls import re_path

from . import consumers


# This as_asgi() works like Django's as_view()
# https://channels.readthedocs.io/en/stable/tutorial/part_2.html
websocket_urlpatterns = [
    re_path(r"ws/powerscan/chat/(?P<room_name>\w+)/$", consumers.ChatConsumer.as_asgi()),
]
