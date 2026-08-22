from typing import TYPE_CHECKING, override

from django.contrib import admin
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from django_gc.forms import GlobalConfigCategoryForm
from django_gc.models import GlobalConfigCategory

if TYPE_CHECKING:
    _GlobalConfigCategoryAdmin = admin.ModelAdmin[GlobalConfigCategory]
else:
    _GlobalConfigCategoryAdmin = admin.ModelAdmin


@admin.register(GlobalConfigCategory)
class GlobalConfigCategoryAdmin(_GlobalConfigCategoryAdmin):
    """
    Разрешить переименование системных категорий без изменения их состава.
    """

    form = GlobalConfigCategoryForm
    list_display = ['id', 'code', 'name']
    search_fields = ['code', 'name']
    ordering = ['id']
    readonly_fields = ['id', 'code', 'created_at', 'updated_at']
    fieldsets = [
        (_('Идентификаторы'), {'classes': ['wide'], 'fields': ['id', 'code']}),
        (_('Категория'), {'classes': ['wide'], 'fields': ['name']}),
        (_('Даты'), {'classes': ['wide'], 'fields': ['created_at', 'updated_at']}),
    ]

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
