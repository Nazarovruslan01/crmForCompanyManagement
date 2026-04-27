"""
ASGI config for CRM project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

# Initialize Django BEFORE importing app modules that depend on the app registry.
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402

from apps.notifications.middleware import JWTAuthMiddleware  # noqa: E402
from apps.notifications.routing import websocket_urlpatterns as notifications_patterns  # noqa: E402

# Combine all WebSocket URL patterns
websocket_urlpatterns = notifications_patterns.copy()

try:
    from apps.messenger.routing import websocket_urlpatterns as messenger_patterns

    websocket_urlpatterns.extend(messenger_patterns)
except ImportError:
    pass  # messenger app may not be available during initial setup

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": JWTAuthMiddleware(URLRouter(websocket_urlpatterns)),
    }
)
