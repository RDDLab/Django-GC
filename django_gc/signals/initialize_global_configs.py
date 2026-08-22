from typing import Any

from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.dispatch import receiver

from django_gc.services import GlobalConfigInitializationService


@receiver(signal=post_migrate, dispatch_uid='django_gc.initialize_from_definitions')
def initialize_global_configs(sender: AppConfig, **kwargs: Any) -> None:
    """
    Инициализировать категории и ключи после миграций приложения GlobalConfig.
    """
    if sender.name != 'django_gc':
        return
    GlobalConfigInitializationService().initialize()
