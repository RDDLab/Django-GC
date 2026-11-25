from typing import TYPE_CHECKING, override

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from django_gc.conf import get_category_definitions
from django_gc.models import GlobalConfigCategory

if TYPE_CHECKING:
    _GlobalConfigCategoryAdmin = admin.ModelAdmin[GlobalConfigCategory]
else:
    _GlobalConfigCategoryAdmin = admin.ModelAdmin


@admin.register(GlobalConfigCategory)
class GlobalConfigCategoryAdmin(_GlobalConfigCategoryAdmin):
    """
    List stored category IDs with codes and names resolved from the active definitions.

    Use the code-owned metadata for display and search without storing duplicate labels in the database.
    """

    list_display = ['id', 'category_code', 'category_name']
    search_fields = ['id']
    ordering = ['id']
    readonly_fields = ['id', 'category_code', 'category_name']
    fieldsets = [
        (_('Identifier'), {'classes': ['wide'], 'fields': ['id']}),
        (_('Category'), {'classes': ['wide'], 'fields': ['category_code', 'category_name']}),
    ]

    @admin.display(description=_('Code'))
    def category_code(self, obj: GlobalConfigCategory) -> str:
        """
        Display the category code resolved from the active definition.
        """
        return obj.code

    @admin.display(description=_('Name'))
    def category_name(self, obj: GlobalConfigCategory) -> str:
        """
        Display the category name resolved from the active definition.
        """
        return obj.name

    @override
    def get_search_results(
        self, request: HttpRequest, queryset: QuerySet[GlobalConfigCategory], search_term: str
    ) -> tuple[QuerySet[GlobalConfigCategory], bool]:
        """
        Match category IDs, codes and display names case-insensitively against the active definitions.

        Apply the resulting IDs to the incoming queryset so existing admin filters still apply.
        """
        normalized_term = search_term.casefold()
        category_ids = [
            item.id
            for item in get_category_definitions()
            if normalized_term
            and (
                normalized_term in str(item.id).casefold()
                or normalized_term in item.code.casefold()
                or normalized_term in item.name.casefold()
            )
        ]
        if not normalized_term:
            return queryset, False
        return queryset.filter(id__in=category_ids), False

    @override
    def has_add_permission(self, request: HttpRequest) -> bool:
        """
        Disable creating categories in the admin. The initialization command creates the declared
        categories.
        """
        return False

    @override
    def has_delete_permission(self, request: HttpRequest, obj: GlobalConfigCategory | None = None) -> bool:
        """
        Disable deleting categories in the admin so the catalog stays consistent with the definitions.
        """
        return False
