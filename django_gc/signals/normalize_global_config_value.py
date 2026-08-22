from datetime import date, datetime, time
from typing import Any

from django.db.models.signals import pre_save
from django.dispatch import receiver

from django_gc.conf import encrypt_value
from django_gc.enums import SettingType
from django_gc.models import GlobalConfig


@receiver(signal=pre_save, sender=GlobalConfig, dispatch_uid='django_gc.normalize_value')
def normalize_global_config_value(sender: type[GlobalConfig], instance: GlobalConfig, raw: bool, **kwargs: Any) -> None:
    """
    Нормализовать изменённое значение перед сохранением без повторного шифрования.
    """
    if raw or instance.value is None:
        return

    value_type = SettingType(instance.value_type)
    if value_type == SettingType.SECURE:
        previous_value: str | None = sender.objects.filter(pk=instance.pk).values_list('value', flat=True).first()
        if previous_value != instance.value:
            instance.value = encrypt_value(text=str(instance.value))
    elif value_type == SettingType.TIME and isinstance(instance.value, time):
        instance.value = instance.value.strftime('%H:%M:%S')
    elif value_type == SettingType.DATETIME and isinstance(instance.value, datetime):
        instance.value = instance.value.strftime('%d.%m.%Y %H:%M:%S')
    elif value_type == SettingType.DATE and isinstance(instance.value, date):
        instance.value = instance.value.strftime('%d.%m.%Y')
