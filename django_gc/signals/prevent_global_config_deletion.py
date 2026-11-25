from typing import Any

from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils.translation import gettext as _

from django_gc.exceptions import GlobalConfigDeletionForbiddenError
from django_gc.models import GlobalConfig


@receiver(signal=pre_delete, sender=GlobalConfig, dispatch_uid='django_gc.prevent_deletion')
def prevent_global_config_deletion(sender: type[GlobalConfig], instance: GlobalConfig, **kwargs: Any) -> None:
    """
    Prevent a declared setting row from being deleted.

    Raise GlobalConfigDeletionForbiddenError with the key of the row the caller tried to delete.
    """
    raise GlobalConfigDeletionForbiddenError(
        _('GlobalConfig setting %(key)s cannot be deleted.') % {'key': instance.key}
    )
