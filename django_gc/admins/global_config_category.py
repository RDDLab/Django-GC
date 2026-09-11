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
    Показать числовые категории и их labels из project definitions.
    """

    list_display = ['id', 'category_code', 'category_name']
    search_fields = ['id']
    ordering = ['id']
    readonly_fields = ['id', 'category_code', 'category_name']
    fieldsets = [
        (_('Идентификатор'), {'classes': ['wide'], 'fields': ['id']}),
        (_('Категория'), {'classes': ['wide'], 'fields': ['category_code', 'category_name']}),
    ]

    @admin.display(description=_('Код'))
    def category_code(self, obj: GlobalConfigCategory) -> str:
        return obj.code

    @admin.display(description=_('Название'))
    def category_name(self, obj: GlobalConfigCategory) -> str:
        return obj.name

    @override
    def get_search_results(
        self, request: HttpRequest, queryset: QuerySet[GlobalConfigCategory], search_term: str
    ) -> tuple[QuerySet[GlobalConfigCategory], bool]:
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
        Разрешить создание категорий только через definitions.
        """
        return False

    @override
    def has_delete_permission(self, request: HttpRequest, obj: GlobalConfigCategory | None = None) -> bool:
        """
        Запретить удаление системных категорий.
        """
        return False
