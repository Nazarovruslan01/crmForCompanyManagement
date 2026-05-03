# pyright: reportCallIssue=false, reportArgumentType=false

"""WebSocket URL routing for messenger app."""

from django.urls import re_path

from .consumers import MessengerConsumer

websocket_urlpatterns = [
    re_path(
        r"ws/messenger/tickets/(?P<ticket_id>\d+)/$",
        MessengerConsumer.as_asgi(),
    ),
]


# pyright: reportCallIssue=false
