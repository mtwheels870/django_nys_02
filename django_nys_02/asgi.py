"""
ASGI config for DJANGO project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter, ChannelNameRouter
from channels.security.websocket import AllowedHostsOriginValidator

from django.core.asgi import get_asgi_application

from powerscan.consumers import TaskConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_nys_02.settings')

# application = get_asgi_application()
django_asgi_app = get_asgi_application()
print(f"django_asgi_app = {django_asgi_app}")

# Our URLs are in here
from powerscan.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(URLRouter(websocket_urlpatterns))),
    'channel': ChannelNameRouter({
        'task-one': TaskConsumer.as_asgi(actions={"generate":"task_one"}),
        'task-two': TaskConsumer.as_asgi(actions={"delete":"task_two"}),
        }),
    })
