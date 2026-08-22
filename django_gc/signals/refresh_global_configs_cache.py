from typing import Any

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from django_gc.conf import is_refresh_suppressed
from django_gc.models import GlobalConfig
from django_gc.signals.callbacks import refresh_global_configs_cache_safely


@receiver(signal=post_save, sender=GlobalConfig, dispatch_uid='django_gc.refresh_cache')
def refresh_global_configs_cache(sender: type[GlobalConfig], using: str, raw: bool, **kwargs: Any) -> None:
    """
    Запланировать полное обновление кэша после любого сохранения GlobalConfig.
    """
    if raw or is_refresh_suppressed():
        return
    transaction.on_commit(refresh_global_configs_cache_safely, using=using)
