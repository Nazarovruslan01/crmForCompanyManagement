from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'

    def ready(self) -> None:
        # Import audit module to connect signals
        from . import audit  # noqa: F401
