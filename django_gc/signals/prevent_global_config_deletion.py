from typing import Any

from django.db.models.signals import pre_delete
from django.dispatch import receiver

from django_gc.exceptions import GlobalConfigDeletionForbiddenError
from django_gc.models import GlobalConfig


@receiver(signal=pre_delete, sender=GlobalConfig, dispatch_uid='django_gc.prevent_deletion')
def prevent_global_config_deletion(sender: type[GlobalConfig], instance: GlobalConfig, **kwargs: Any) -> None:
    """
    Запретить удаление однажды созданного системного ключа.
    """
    raise GlobalConfigDeletionForbiddenError(f'Ключ <{instance.key}> нельзя удалить.')
