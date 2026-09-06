from functools import partial
from typing import Any

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from django_gc.conf import is_refresh_suppressed
from django_gc.models import GlobalConfig
from django_gc.signals.callbacks import refresh_global_config_value_safely


@receiver(signal=post_save, sender=GlobalConfig, dispatch_uid='django_gc.refresh_cache')
def refresh_global_configs_cache(
    sender: type[GlobalConfig], instance: GlobalConfig, using: str, raw: bool, **kwargs: Any
) -> None:
    """
    Запланировать точечное обновление изменённого ключа после commit.
    """
    if raw or is_refresh_suppressed():
        return
    transaction.on_commit(partial(refresh_global_config_value_safely, changed_key=str(instance.key)), using=using)
