from ast import literal_eval
from typing import Any, ClassVar

from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from django_gc.conf import encrypt_value, get_category_definitions, get_setting_definitions, suppress_cache_refresh
from django_gc.dto import SettingDefinition
from django_gc.enums import SettingType
from django_gc.models import GlobalConfig, GlobalConfigCategory
from django_gc.singleton import Singleton
from django_gc.utils import table_exists


class GlobalConfigInitializationService(Singleton):
    """
    Synchronize code-declared categories and settings with the database.

    Explicit initialization creates missing rows and updates managed metadata while preserving values
    already in use.
    """

    ARRAY_TYPES: ClassVar[frozenset[SettingType]] = frozenset(
        {SettingType.STRING_ARRAY, SettingType.FLOAT_ARRAY, SettingType.INTEGER_ARRAY, SettingType.DECIMAL_ARRAY}
    )
    CHOICE_TYPES: ClassVar[frozenset[SettingType]] = frozenset(
        {
            SettingType.FLOAT_CHOICES,
            SettingType.INTEGER_CHOICES,
            SettingType.STRING_CHOICES,
            SettingType.DECIMAL_CHOICES,
            SettingType.INTEGER_MULTIPLE_CHOICES,
            SettingType.STRING_MULTIPLE_CHOICES,
            SettingType.FLOAT_MULTIPLE_CHOICES,
        }
    )

    @transaction.atomic
    def initialize(self) -> None:
        """
        Apply the active definitions in a transaction when both configuration tables exist.

        Suppress per-row cache refresh callbacks and schedule a full refresh after commit.
        """
        required_tables = [GlobalConfig._meta.db_table, GlobalConfigCategory._meta.db_table]
        if not all(table_exists(table_name=table_name) for table_name in required_tables):
            return

        with suppress_cache_refresh():
            self._create_missing_categories()
            self._synchronize_configs()

        from django_gc.signals.callbacks import refresh_global_configs_cache_safely

        transaction.on_commit(refresh_global_configs_cache_safely)

    @classmethod
    def _create_missing_categories(cls) -> None:
        """
        Insert rows for declared category IDs absent from the database.
        """
        existing_ids: set[int] = set(GlobalConfigCategory.objects.values_list('id', flat=True))
        categories = [
            GlobalConfigCategory(id=item.id) for item in get_category_definitions() if item.id not in existing_ids
        ]
        if categories:
            GlobalConfigCategory.objects.bulk_create(categories)

    def _synchronize_configs(self) -> None:
        """
        Lock existing settings, update their managed metadata and insert missing keys.

        Reuse declared previous values when the canonical key is absent. Reject conflicting values or
        previous rows with a different type.
        """
        existing_configs: dict[str, GlobalConfig] = {
            config.key: config
            for config in GlobalConfig.objects.select_for_update().select_related('category').order_by('pk')
        }
        categories_by_id: dict[int, GlobalConfigCategory] = GlobalConfigCategory.objects.in_bulk()
        new_configs: list[GlobalConfig] = []

        for item in get_setting_definitions():
            try:
                category = categories_by_id[item.category_id]
            except KeyError:
                raise KeyError(
                    _('GlobalConfig category id=%(category_id)s is not declared.')
                    % {'category_id': item.category_id}
                ) from None
            config = existing_configs.get(str(item.key))
            if config is None:
                previous = [existing_configs[key] for key in item.previous_keys if key in existing_configs]
                if previous:
                    if any(row.value != previous[0].value for row in previous[1:]):
                        raise ValueError(f'Conflicting previous values for GlobalConfig key {item.key!s}.')
                    if any(row.value_type != item.value_type for row in previous):
                        raise ValueError(f'Previous value type differs for GlobalConfig key {item.key!s}.')
                new_configs.append(self._build_config(
                    item=item, category=category, previous=previous[0] if previous else None
                ))
                continue

            self._update_metadata(config=config, item=item, category=category)

        if new_configs:
            GlobalConfig.objects.bulk_create(new_configs)

    @classmethod
    def _build_config(
        cls, item: SettingDefinition, category: GlobalConfigCategory, previous: GlobalConfig | None = None
    ) -> GlobalConfig:
        """
        Build an unsaved settings row from a definition and its category.

        Reuse the raw value from a previous row when provided. Otherwise, prepare the default for storage.
        """
        return GlobalConfig(
            key=str(item.key),
            description=item.description,
            value=previous.value if previous is not None else cls._prepare_default_value(item=item),
            value_type=item.value_type,
            category=category,
            nullable=item.nullable,
            is_read_only=item.is_read_only,
            variables=item.variables,
            is_always_update=item.is_always_update,
        )

    @classmethod
    def _update_metadata(cls, config: GlobalConfig, item: SettingDefinition, category: GlobalConfigCategory) -> None:
        """
        Update the fields managed by the active definition and leave the stored value intact.

        Replace choice options only for choice types with is_always_update enabled. Save when a managed
        field actually changes.
        """
        if item.is_always_update and item.value_type in cls.CHOICE_TYPES:
            variables = item.variables
        else:
            variables = config.variables
        changed_fields: list[str] = []
        managed_values: dict[str, Any] = {
            'description': item.description,
            'value_type': item.value_type,
            'category': category,
            'nullable': item.nullable,
            'is_read_only': item.is_read_only,
            'variables': variables,
            'is_always_update': item.is_always_update,
        }
        for field_name, value in managed_values.items():
            if getattr(config, field_name) != value:
                setattr(config, field_name, value)
                changed_fields.append(field_name)

        if changed_fields:
            config.updated_at = timezone.now()
            config.save(update_fields=[*changed_fields, 'updated_at'])

    @classmethod
    def _prepare_default_value(cls, item: SettingDefinition) -> Any:
        """
        Prepare the initial value when there is no previous row to reuse.

        Consult the owning provider when present. Apply the storage rules for secure values, arrays and
        provider-supplied JSON.
        """
        from django_gc.registry import get_provider

        provider = get_provider(key=str(item.key))
        default = item.default_value if provider is None else provider.initial_value(
            key=str(item.key), default=item.default_value
        )
        if provider is not None and item.value_type == SettingType.JSON:
            import json

            return json.dumps(default)
        if item.value_type == SettingType.SECURE:
            return encrypt_value(text=str(default))
        if item.value_type not in cls.ARRAY_TYPES:
            return default
        try:
            values = literal_eval(str(default))
        except (ValueError, SyntaxError):
            return default
        return ';'.join(map(str, values))
