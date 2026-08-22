from typing import Any, override

from django.db import models
from django.utils.translation import gettext_lazy as _

from django_gc.enums import SettingType
from django_gc.exceptions import GlobalConfigCreationForbiddenError
from django_gc.models.global_config_category import GlobalConfigCategory


class GlobalConfig(models.Model):
    """
    Хранить исходные значения глобальных конфигураций и их метаданные.

    Бизнес-код получает типизированные значения только через GlobalConfigService.
    """

    key = models.TextField(primary_key=True, verbose_name=_('Ключ'))
    value = models.TextField(null=True, blank=True, verbose_name=_('Значение'))
    category = models.ForeignKey(
        to=GlobalConfigCategory, on_delete=models.PROTECT, related_name='settings', verbose_name=_('Категория')
    )
    value_type = models.SmallIntegerField(choices=SettingType.choices(), verbose_name=_('Тип значения'))
    description = models.TextField(blank=True, null=True, verbose_name=_('Описание'))
    is_read_only = models.BooleanField(default=False, verbose_name=_('Только для чтения'))
    nullable = models.BooleanField(default=False, verbose_name=_('Может ли быть не заполнено'))
    variables = models.JSONField(null=True, blank=True, verbose_name=_('Возможные значения'))
    is_always_update = models.BooleanField(
        default=False, help_text=_('Только для типов данных с выбором значения.'), verbose_name=_('Всегда обновляемый')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Дата создания'))
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True, verbose_name=_('Дата изменения'))

    @property
    def meaningless(self) -> bool:
        """
        Проверить отсутствие обязательного значения.
        """
        return (self.value is None or self.value == '') and not self.nullable

    @property
    def choices(self) -> list[tuple[Any, str]]:
        """
        Подготовить варианты значения для Django Admin.
        """
        if self.variables is None:
            return []
        return [(value, key) for key, value in self.variables.items()]

    @override
    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Запретить создание новых ключей вне проектных definitions.
        """
        if self._state.adding:
            raise GlobalConfigCreationForbiddenError(f'Ключ <{self.key}> можно создать только через definitions.')
        if not type(self).objects.filter(pk=self.pk).exists():
            raise GlobalConfigCreationForbiddenError(f'Ключ <{self.key}> нельзя изменять или создавать вручную.')
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.key

    class Meta:
        db_table = 'global_configs'
        verbose_name = _('Глобальная конфигурация')
        verbose_name_plural = _('Глобальные конфигурации')
        default_permissions = ['change', 'view']
