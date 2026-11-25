from typing import Any, override

from django.core.exceptions import PermissionDenied
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

from django_gc.enums import SettingType
from django_gc.exceptions import GlobalConfigCreationForbiddenError
from django_gc.models.global_config_category import GlobalConfigCategory


class GlobalConfig(models.Model):
    """
    Store a declared setting's serialized value and editor metadata under its canonical key.

    Application code reads typed values through the runtime API or GlobalConfigService.
    """

    key = models.TextField(primary_key=True, verbose_name=_('Key'))
    value = models.TextField(null=True, blank=True, verbose_name=_('Value'))
    category = models.ForeignKey(
        to=GlobalConfigCategory, on_delete=models.PROTECT, related_name='settings', verbose_name=_('Category')
    )
    value_type = models.SmallIntegerField(choices=SettingType.choices(), verbose_name=_('Value type'))
    description = models.TextField(blank=True, null=True, verbose_name=_('Description'))
    is_read_only = models.BooleanField(default=False, verbose_name=_('Read-only'))
    nullable = models.BooleanField(default=False, verbose_name=_('Allow empty values'))
    variables = models.JSONField(null=True, blank=True, verbose_name=_('Allowed choices'))
    is_always_update = models.BooleanField(
        default=False,
        help_text=_('During initialization, replace the options for choice settings with the declared options.'),
        verbose_name=_('Always update choices'),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created at'))
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True, verbose_name=_('Updated at'))

    @property
    def meaningless(self) -> bool:
        """
        Return whether a setting requires a value and currently contains None or an empty string.
        """
        return (self.value is None or self.value == '') and not self.nullable

    @property
    def choices(self) -> list[tuple[Any, str]]:
        """
        Convert stored label-to-value mappings into Django's value-and-label pairs.

        Return an empty list when the setting has no choices.
        """
        if self.variables is None:
            return []
        return [(value, key) for key, value in self.variables.items()]

    @override
    @transaction.atomic
    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Save an existing setting after enforcing read-only and provider rules.

        Reject manually inserted or renamed keys. Validate changed provider-owned values within the save
        transaction.
        """
        if self._state.adding:
            raise GlobalConfigCreationForbiddenError(
                _('GlobalConfig setting %(key)s must be created by initializing its definition.')
                % {'key': self.key}
            )
        if not type(self).objects.filter(pk=self.pk).exists():
            raise GlobalConfigCreationForbiddenError(
                _('GlobalConfig setting %(key)s cannot be created or renamed manually.') % {'key': self.key}
            )
        from django_gc.registry import get_provider, validate_change
        from django_gc.services import GlobalConfigService

        previous = type(self).objects.only('value', 'is_read_only').get(pk=self.pk)
        if previous.is_read_only and previous.value != self.value:
            raise PermissionDenied(_('This setting is read-only.'))
        if previous.value != self.value and get_provider(key=self.key) is not None:
            typed_value = GlobalConfigService.parse_value(config=self)
            validate_change(key=self.key, value=typed_value)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.key

    class Meta:
        db_table = 'global_configs'
        verbose_name = _('Global setting')
        verbose_name_plural = _('Global settings')
        default_permissions = ['change', 'view']
