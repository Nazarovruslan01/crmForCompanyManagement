"""
ASGI config for CRM project.
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

from apps.notifications.middleware import JWTAuthMiddleware
from apps.notifications.routing import websocket_urlpatterns as notifications_patterns

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

# Combine all WebSocket URL patterns
websocket_urlpatterns = notifications_patterns.copy()

try:
    from apps.messenger.routing import websocket_urlpatterns as messenger_patterns

    websocket_urlpatterns.extend(messenger_patterns)
except ImportError:
    pass  # messenger app may not be available during initial setup

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": JWTAuthMiddleware(URLRouter(websocket_urlpatterns)),
    }
)
