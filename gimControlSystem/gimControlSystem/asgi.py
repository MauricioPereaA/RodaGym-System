"""
ASGI config for gimControlSystem project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import acceso.routing  # Asegúrate de crear este archivo

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gimControlSystem.settings')

application = ProtocolTypeRouter({
  "http": get_asgi_application(),
  # Just HTTP for now. (We can add other protocols later.)
  "websocket": AuthMiddlewareStack(
        URLRouter(
            acceso.routing.websocket_urlpatterns
        )
    ),
})