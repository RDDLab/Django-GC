from django.db import models
from django.utils.translation import gettext_lazy as _

from django_gc.conf import get_category_definition


class GlobalConfigCategory(models.Model):
    """
    Хранить числовой идентификатор системной категории.

    Код и отображаемое название принадлежат project definitions и в БД не
    дублируются.
    """

    id = models.PositiveSmallIntegerField(primary_key=True, editable=False, verbose_name=_('ID'))

    @property
    def code(self) -> str:
        """
        Получить код категории из project definitions.
        """
        definition = get_category_definition(category_id=self.id)
        return definition.code if definition is not None else str(self.id)

    @property
    def name(self) -> str:
        """
        Получить отображаемое название категории из project definitions.
        """
        definition = get_category_definition(category_id=self.id)
        return definition.name if definition is not None else str(self.id)

    def __str__(self) -> str:
        return self.name

    class Meta:
        db_table = 'global_config_categories'
        verbose_name = _('Категория глобальных конфигураций')
        verbose_name_plural = _('Категории глобальных конфигураций')
        ordering = ['id']
        default_permissions = ['change', 'view']
