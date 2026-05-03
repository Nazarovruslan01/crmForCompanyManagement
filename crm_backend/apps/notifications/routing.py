# pyright: reportCallIssue=false, reportArgumentType=false

"""WebSocket URL routing for notifications app."""

from django.urls import re_path

from .consumers import NotificationConsumer

websocket_urlpatterns = [
    re_path(r"ws/notifications/$", NotificationConsumer.as_asgi()),
]


# pyright: reportCallIssue=false
