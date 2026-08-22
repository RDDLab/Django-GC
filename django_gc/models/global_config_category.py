from django.db import models
from django.utils.translation import gettext_lazy as _


class GlobalConfigCategory(models.Model):
    """
    Редактируемая категория системных глобальных настроек.
    """

    id = models.PositiveSmallIntegerField(primary_key=True, editable=False, verbose_name=_('ID'))
    code = models.SlugField(max_length=64, unique=True, editable=False, verbose_name=_('Код'))
    name = models.TextField(verbose_name=_('Название'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Дата создания'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Дата изменения'))

    def __str__(self) -> str:
        return self.name

    class Meta:
        db_table = 'global_config_categories'
        verbose_name = _('Категория глобальных конфигураций')
        verbose_name_plural = _('Категории глобальных конфигураций')
        ordering = ['id']
        default_permissions = ['change', 'view']
