from typing import override

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class Config(AppConfig):
    """
    Register Django-GC as the application for typed runtime settings.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'django_gc'
    verbose_name = _('Settings management')

    @override
    def ready(self) -> None:
        """
        Register the model signal receivers and the standard Django Admin classes when Django loads the app.
        """
        from django_gc import admins, signals
