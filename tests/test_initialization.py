from django.test import TestCase, override_settings

from django_gc.dto import CategoryDefinition, SettingDefinition
from django_gc.models import GlobalConfig, GlobalConfigCategory
from django_gc.services import GlobalConfigInitializationService
from django_gc.signals.refresh_global_configs_cache import refresh_global_configs_cache
from tests.definitions import TEST_CATEGORIES, TEST_DEFINITIONS


class GlobalConfigInitializationTestCase(TestCase):
    """
    Проверить синхронизацию definitions без перезаписи рабочих значений.
    """

    def test_initialize_creates_declared_categories_and_keys(self) -> None:
        """
        Создать все объявленные категории и ключи.
        """
        self.assertEqual(GlobalConfigCategory.objects.count(), len(TEST_CATEGORIES))
        self.assertEqual(GlobalConfig.objects.count(), len(TEST_DEFINITIONS))

    def test_initialize_preserves_live_value(self) -> None:
        """
        Не перезаписывать уже изменённое рабочее значение.
        """
        config = GlobalConfig.objects.get(pk='platform-pagination-size')
        config.value = '99'
        config.save(update_fields=['value', 'updated_at'])

        GlobalConfigInitializationService().initialize()

        config.refresh_from_db()
        self.assertEqual(config.value, '99')

    def test_initialize_preserves_renamed_category(self) -> None:
        """
        Сохранить ручное название категории.
        """
        category = GlobalConfigCategory.objects.get(pk=1)
        category.name = 'Renamed'
        category.save(update_fields=['name', 'updated_at'])

        GlobalConfigInitializationService().initialize()

        category.refresh_from_db()
        self.assertEqual(category.name, 'Renamed')

    def test_initialize_updates_metadata_only(self) -> None:
        """
        Обновить description без смены value.
        """
        updated_definitions = [
            SettingDefinition(
                key=item.key,
                description='Updated description' if str(item.key) == 'platform-pagination-size' else item.description,
                default_value=item.default_value,
                value_type=item.value_type,
                category_id=item.category_id,
                nullable=item.nullable,
                is_read_only=item.is_read_only,
                variables=item.variables,
                is_always_update=item.is_always_update,
            )
            for item in TEST_DEFINITIONS
        ]
        with override_settings(GLOBAL_CONFIG_DEFINITIONS=updated_definitions):
            GlobalConfigInitializationService().initialize()

        config = GlobalConfig.objects.get(pk='platform-pagination-size')
        self.assertEqual(config.description, 'Updated description')
        self.assertEqual(config.value, '25')

    def test_initialize_does_not_schedule_per_row_refresh(self) -> None:
        """
        Подавить post_save refresh во время синхронизации метаданных.
        """
        updated_definitions = [
            SettingDefinition(
                key=item.key,
                description=f'{item.description} changed',
                default_value=item.default_value,
                value_type=item.value_type,
                category_id=item.category_id,
                nullable=item.nullable,
                is_read_only=item.is_read_only,
                variables=item.variables,
                is_always_update=item.is_always_update,
            )
            for item in TEST_DEFINITIONS
        ]
        with (
            override_settings(GLOBAL_CONFIG_DEFINITIONS=updated_definitions),
            self.captureOnCommitCallbacks() as callbacks,
        ):
            GlobalConfigInitializationService().initialize()

        refresh_callbacks = [callback for callback in callbacks if callback is refresh_global_configs_cache]
        self.assertEqual(refresh_callbacks, [])

    def test_always_update_replaces_choice_variables(self) -> None:
        """
        Обновить choices только при is_always_update.
        """
        updated_definitions = [
            SettingDefinition(
                key=item.key,
                description=item.description,
                default_value=item.default_value,
                value_type=item.value_type,
                category_id=item.category_id,
                nullable=item.nullable,
                is_read_only=item.is_read_only,
                variables=(
                    {'Dark': 'dark', 'Light': 'light', 'System': 'system'}
                    if str(item.key) == 'theme-choice'
                    else item.variables
                ),
                is_always_update=item.is_always_update,
            )
            for item in TEST_DEFINITIONS
        ]
        with override_settings(GLOBAL_CONFIG_DEFINITIONS=updated_definitions):
            GlobalConfigInitializationService().initialize()

        config = GlobalConfig.objects.get(pk='theme-choice')
        self.assertEqual(config.variables, {'Dark': 'dark', 'Light': 'light', 'System': 'system'})

    def test_new_category_is_created_from_definitions(self) -> None:
        """
        Добавить новую категорию без удаления существующих.
        """
        extra_categories = [*TEST_CATEGORIES, CategoryDefinition(id=9, code='reports', name='Reports')]
        with override_settings(GLOBAL_CONFIG_CATEGORIES=extra_categories):
            GlobalConfigInitializationService().initialize()

        self.assertTrue(GlobalConfigCategory.objects.filter(pk=9, code='reports').exists())
        self.assertEqual(GlobalConfigCategory.objects.count(), 3)
