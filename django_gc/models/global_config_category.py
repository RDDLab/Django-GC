from django.db import models
from django.utils.translation import gettext_lazy as _

from django_gc.conf import get_category_definition


class GlobalConfigCategory(models.Model):
    """
    Store the numeric ID of a setting category.

    Read codes and display names from the active definitions so the database stores only the identifier.
    """

    id = models.PositiveSmallIntegerField(primary_key=True, editable=False, verbose_name=_('ID'))

    @property
    def code(self) -> str:
        """
        Return the declared category code, using the numeric ID as text if the definition is unavailable.
        """
        definition = get_category_definition(category_id=self.id)
        return definition.code if definition is not None else str(self.id)

    @property
    def name(self) -> str:
        """
        Return the declared display name, using the numeric ID as text if the definition is unavailable.
        """
        definition = get_category_definition(category_id=self.id)
        return definition.name if definition is not None else str(self.id)

    def __str__(self) -> str:
        return self.name

    class Meta:
        db_table = 'global_config_categories'
        verbose_name = _('Global settings category')
        verbose_name_plural = _('Global settings categories')
        ordering = ['id']
        default_permissions = ['change', 'view']
