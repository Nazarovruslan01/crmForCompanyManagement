"""URL configuration for messenger app."""

from django.urls import path

from .views import TelegramWebhookView

app_name = "messenger"

urlpatterns = [
    path("telegram/webhook/", TelegramWebhookView.as_view(), name="telegram-webhook"),
]
