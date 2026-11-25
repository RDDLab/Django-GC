import json
from typing import TYPE_CHECKING, Any, override

from django.contrib import admin
from django.contrib.admin.utils import unquote
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from django_gc.conf import get_category_definitions, get_setting_definitions
from django_gc.enums import SettingType
from django_gc.forms import GlobalConfigForm
from django_gc.models import GlobalConfig
from django_gc.registry import get_provider, get_providers

if TYPE_CHECKING:
    from django.contrib.admin.options import _FieldsetSpec

    _GlobalConfigAdmin = admin.ModelAdmin[GlobalConfig]
else:
    _GlobalConfigAdmin = admin.ModelAdmin


@admin.register(GlobalConfig)
class GlobalConfigAdmin(_GlobalConfigAdmin):
    """
    Administer values for declared settings in Django Admin.

    The catalog lists active definitions the operator can view. Value edits also respect read-only metadata
    and the owning provider's access rules.
    """

    form = GlobalConfigForm
    VALUE_PREVIEW_LENGTH = 120

    list_display = ['setting_description', 'setting_value', 'value_type', 'key', 'category']
    list_select_related = ['category']
    list_filter = [('category', admin.RelatedOnlyFieldListFilter), 'value_type', 'is_read_only']
    search_fields = ['key', 'description']
    ordering = ['category', 'description']
    readonly_fields = [
        'key', 'description', 'setting_description', 'value_type', 'is_read_only', 'category',
        'created_at', 'updated_at', 'setting_value',
    ]
    fieldsets = [
        (_('General information'), {
            'classes': ['wide'], 'fields': ['key', 'category', 'value_type', 'setting_description'],
        }),
        (_('Options'), {'classes': ['wide'], 'fields': ['is_read_only']}),
        (_('Value'), {'classes': ['wide'], 'fields': ['value']}),
        (_('Dates'), {'classes': ['wide'], 'fields': ['created_at', 'updated_at']}),
    ]

    @admin.display(description=_('Value'))
    def setting_value(self, config: GlobalConfig) -> str:
        """
        Show a short display value using fields already loaded for the row.

        Boolean values get localized labels. Secure values are always masked in the list.
        """
        if config.value_type == SettingType.SECURE:
            return '••••••••'
        from django_gc.services import GlobalConfigService

        value = GlobalConfigService.parse_value(config=config)
        if value is None:
            return '—'
        if isinstance(value, bool):
            return str(_('Enabled') if value else _('Disabled'))
        for choice, label in config.choices:
            if value == choice:
                return gettext(label)
        text = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)
        return text if len(text) <= self.VALUE_PREVIEW_LENGTH else f'{text[:self.VALUE_PREVIEW_LENGTH - 1]}…'

    @admin.display(description=_('Description'))
    def setting_description(self, config: GlobalConfig) -> str:
        """
        Translate the stored description for the active language.

        Look up the description as a message ID at render time so a single database value can serve multiple
        locales.
        """
        return gettext(config.description) if config.description else ''

    @override
    def get_queryset(self, request: HttpRequest) -> QuerySet[GlobalConfig]:
        """
        Limit the admin catalog to declared keys visible to the requesting operator.
        """
        visible_keys = {str(item.key) for item in get_setting_definitions()}
        can_change = self.has_change_permission(request)
        for provider, registration in get_providers():
            if provider.has_view_permission(request=request):
                continue
            may_change_provider = can_change and provider.has_change_permission(request=request)
            visible_keys.difference_update(
                str(item.key)
                for item in provider.get_definitions(category_ids=registration.category_ids)
                if not may_change_provider or item.is_read_only
            )
        return super().get_queryset(request).filter(key__in=visible_keys)

    @override
    def get_object(self, request: HttpRequest, object_id: str, from_field: str | None = None) -> GlobalConfig | None:
        """
        Resolve an individual admin record against the visible catalog.

        When a provider denies direct access to a hidden key, raise PermissionDenied so the response is HTTP
        403.
        """
        config = super().get_object(request, object_id, from_field)
        if config is not None or from_field not in {None, 'key'}:
            return config
        provider = get_provider(key=object_id)
        if provider is not None and not (
            (self.has_view_permission(request) and provider.has_view_permission(request=request))
            or (self.has_change_permission(request) and provider.has_change_permission(request=request))
        ):
            raise PermissionDenied
        return None

    @override
    def get_fieldsets(
        self, request: HttpRequest, obj: GlobalConfig | None = None
    ) -> '_FieldsetSpec':
        """
        Replace the value field with a masked display for secure settings the operator can only view.
        """
        fieldsets = super().get_fieldsets(request, obj)
        if obj is None or obj.value_type != SettingType.SECURE or self.has_change_permission(request, obj):
            return fieldsets
        safe_fieldsets = []
        for title, options in fieldsets:
            masked = options.copy()
            masked['fields'] = ['setting_value' if name == 'value' else name for name in options['fields']]
            safe_fieldsets.append((title, masked))
        return safe_fieldsets

    @override
    def lookup_allowed(self, lookup: str, value: str, request: HttpRequest) -> bool:
        """
        Block lookups on the stored value to keep sensitive data out of admin filters.
        """
        return lookup != 'value' and not lookup.startswith('value__') and super().lookup_allowed(lookup, value, request)

    @override
    def change_view(
        self, request: HttpRequest, object_id: str, form_url: str = '', extra_context: dict[str, Any] | None = None
    ) -> HttpResponse:
        """
        Dispatch edits to the owning provider after checking Django Admin permissions.

        Use the standard page when the provider supplies no response. Reject protected POST requests without
        a custom response.
        """
        config = self.get_object(request, unquote(object_id))
        if config is not None:
            if not self.has_view_or_change_permission(request, config):
                raise PermissionDenied
            if request.method == 'POST' and not self.has_change_permission(request, config):
                raise PermissionDenied
            provider = get_provider(key=config.key)
            if provider is not None:
                response = provider.change_view(admin_site=self.admin_site, request=request, key=config.key)
                if response is not None:
                    return response
                if provider.protected and request.method == 'POST':
                    raise PermissionDenied
        return super().change_view(request, object_id, form_url, extra_context)

    @override
    def get_search_results(
        self, request: HttpRequest, queryset: QuerySet[GlobalConfig], search_term: str
    ) -> tuple[QuerySet[GlobalConfig], bool]:
        """
        Extend standard admin search with category codes, names and translated descriptions.
        """
        base_queryset = queryset
        queryset, use_distinct = super().get_search_results(request=request, queryset=queryset, search_term=search_term)
        normalized_term = search_term.casefold()
        category_ids = [
            item.id
            for item in get_category_definitions()
            if normalized_term and (normalized_term in item.code.casefold() or normalized_term in item.name.casefold())
        ]
        if category_ids:
            queryset |= base_queryset.filter(category_id__in=category_ids)
        translated_keys = [str(item.key) for item in get_setting_definitions()
                           if normalized_term and normalized_term in gettext(item.description).casefold()]
        if translated_keys:
            queryset |= base_queryset.filter(key__in=translated_keys)
        return queryset, use_distinct

    @override
    def has_view_permission(self, request: HttpRequest, obj: GlobalConfig | None = None) -> bool:
        """
        Require both the Django Admin view grant and the owning provider's view permission for the record.
        """
        provider = get_provider(key=obj.key) if obj is not None else None
        return super().has_view_permission(request, obj) and (
            provider is None or provider.has_view_permission(request=request)
        )

    @override
    def has_change_permission(self, request: HttpRequest, obj: GlobalConfig | None = None) -> bool:
        """
        Require the Django Admin change grant and the provider's edit permission for an individual setting.

        A setting marked read-only remains unavailable for editing.
        """
        if obj is not None and obj.is_read_only:
            return False
        provider = get_provider(key=obj.key) if obj is not None else None
        return super().has_change_permission(request, obj) and (
            provider is None or provider.has_change_permission(request=request)
        )

    @override
    def has_add_permission(self, request: HttpRequest) -> bool:
        """
        Disable adding settings in the admin. The initialization command creates rows from declared
        definitions.
        """
        return False

    @override
    def has_delete_permission(self, request: HttpRequest, obj: GlobalConfig | None = None) -> bool:
        """
        Disable deleting settings in the admin so initialized keys remain available to application code.
        """
        return False
