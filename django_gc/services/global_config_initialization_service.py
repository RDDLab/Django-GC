from ast import literal_eval
from typing import Any, ClassVar

from django.db import transaction
from django.utils import timezone

from django_gc.conf import encrypt_value, get_category_definitions, get_setting_definitions, suppress_cache_refresh
from django_gc.dto import SettingDefinition
from django_gc.enums import SettingType
from django_gc.models import GlobalConfig, GlobalConfigCategory
from django_gc.singleton import Singleton
from django_gc.utils import table_exists


class GlobalConfigInitializationService(Singleton):
    """
    Синхронизировать управляемые кодом категории и ключи GlobalConfig.
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
        Создать отсутствующие definitions и обновить кодовые метаданные ключей.
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
        Создать только отсутствующие категории, сохранив ручные изменения названий.
        """
        existing_ids: set[int] = set(GlobalConfigCategory.objects.values_list('id', flat=True))
        categories = [
            GlobalConfigCategory(id=item.id, code=item.code, name=item.name)
            for item in get_category_definitions()
            if item.id not in existing_ids
        ]
        if categories:
            GlobalConfigCategory.objects.bulk_create(categories)

    def _synchronize_configs(self) -> None:
        """
        Создать новые ключи и синхронизировать метаданные существующих ключей.
        """
        existing_configs: dict[str, GlobalConfig] = {
            config.key: config for config in GlobalConfig.objects.select_related('category')
        }
        categories_by_id: dict[int, GlobalConfigCategory] = GlobalConfigCategory.objects.in_bulk()
        new_configs: list[GlobalConfig] = []

        for item in get_setting_definitions():
            category: GlobalConfigCategory = categories_by_id[item.category_id]
            config = existing_configs.get(str(item.key))
            if config is None:
                new_configs.append(self._build_config(item=item, category=category))
                continue

            self._update_metadata(config=config, item=item, category=category)

        if new_configs:
            GlobalConfig.objects.bulk_create(new_configs)

    @classmethod
    def _build_config(cls, item: SettingDefinition, category: GlobalConfigCategory) -> GlobalConfig:
        """
        Построить новую модель конфигурации из definitions.
        """
        return GlobalConfig(
            key=str(item.key),
            description=item.description,
            value=cls._prepare_default_value(item=item),
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
        Обновить только управляемые кодом метаданные, не меняя рабочее значение.
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
        Подготовить начальное строковое представление значения для БД.
        """
        if item.value_type == SettingType.SECURE:
            return encrypt_value(text=str(item.default_value))
        if item.value_type not in cls.ARRAY_TYPES:
            return item.default_value
        try:
            values = literal_eval(str(item.default_value))
        except (ValueError, SyntaxError):
            return item.default_value
        return ';'.join(map(str, values))
