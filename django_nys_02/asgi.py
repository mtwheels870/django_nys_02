"""
ASGI config for DJANGO project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_nys_02.settings')

# application = get_asgi_application()
django_asgi_app = get_asgi_application()
print(f"django_asgi_app = {django_asgi_app}")

application = ProtocolTypeRouter({
    "http": django_asgi_app,
})
