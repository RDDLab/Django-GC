from typing import TYPE_CHECKING, override

from django.contrib import admin
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from django_gc.forms import GlobalConfigForm
from django_gc.models import GlobalConfig

if TYPE_CHECKING:
    _GlobalConfigAdmin = admin.ModelAdmin[GlobalConfig]
else:
    _GlobalConfigAdmin = admin.ModelAdmin


@admin.register(GlobalConfig)
class GlobalConfigAdmin(_GlobalConfigAdmin):
    """
    Управлять значениями GlobalConfig без изменения состава системных ключей.
    """

    form = GlobalConfigForm
    list_display = ['key', 'description', 'category']
    list_select_related = ['category']
    list_filter = ['category', 'value_type', 'is_read_only']
    search_fields = ['key', 'description']
    ordering = ['category', 'description']
    readonly_fields = ['key', 'description', 'is_read_only', 'category', 'created_at', 'updated_at']
    fieldsets = [
        (_('Общая информация'), {'classes': ['wide'], 'fields': ['key', 'category', 'value_type', 'description']}),
        (_('Параметры'), {'classes': ['wide'], 'fields': ['is_read_only']}),
        (_('Значение'), {'classes': ['wide'], 'fields': ['value']}),
        (_('Даты'), {'classes': ['wide'], 'fields': ['created_at', 'updated_at']}),
    ]

    @override
    def has_add_permission(self, request: HttpRequest) -> bool:
        """
        Разрешить создание ключей только через definitions.
        """
        return False

    @override
    def has_delete_permission(self, request: HttpRequest, obj: GlobalConfig | None = None) -> bool:
        """
        Запретить удаление системных ключей.
        """
        return False
