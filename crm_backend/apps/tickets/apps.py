from django.apps import AppConfig


class TicketsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.tickets'

    def ready(self) -> None:
        # Import signals to connect receivers
        from . import signals  # noqa: F401
