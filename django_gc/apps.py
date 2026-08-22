from typing import override

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class Config(AppConfig):
    """
    Приложение типизированных runtime-настроек.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'django_gc'
    verbose_name = _('Управление настройками')

    @override
    def ready(self) -> None:
        """
        Подключить сигналы и регистрацию Admin.
        """
        from django_gc import admins, signals
