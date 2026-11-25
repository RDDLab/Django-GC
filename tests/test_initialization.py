from django.test import TestCase, override_settings

from django_gc.dto import CategoryDefinition, SettingDefinition
from django_gc.models import GlobalConfig, GlobalConfigCategory
from django_gc.services import GlobalConfigInitializationService
from django_gc.signals.refresh_global_configs_cache import refresh_global_configs_cache
from tests.definitions import TEST_CATEGORIES, TEST_DEFINITIONS


class GlobalConfigInitializationTestCase(TestCase):
    """
    Verify explicit synchronization against existing database rows.

    Cover creation, metadata reconciliation and preservation of settings that have already been edited.
    """

    def test_initialize_creates_numeric_categories_and_declared_keys(self) -> None:
        """
        Initialize the catalog and verify that each declared key points to its numeric category row.
        """
        self.assertEqual(GlobalConfigCategory.objects.count(), len(TEST_CATEGORIES))
        self.assertSetEqual(set(GlobalConfigCategory.objects.values_list('id', flat=True)), {1, 2})
        self.assertEqual(GlobalConfig.objects.count(), len(TEST_DEFINITIONS))

    def test_category_table_does_not_duplicate_definition_metadata(self) -> None:
        """
        Verify that category codes and names remain code-owned and the database stores only the primary key.
        """
        field_names = {field.name for field in GlobalConfigCategory._meta.local_fields}
        self.assertSetEqual(field_names, {'id'})
        category = GlobalConfigCategory.objects.get(pk=1)
        self.assertEqual(category.code, 'platform')
        self.assertEqual(category.name, 'Platform')

    def test_initialize_preserves_live_value(self) -> None:
        """
        Modify a setting, run initialization again and check that the modified value remains in place.
        """
        config = GlobalConfig.objects.get(pk='platform.pagination_size')
        config.value = '99'
        config.save(update_fields=['value', 'updated_at'])

        GlobalConfigInitializationService().initialize()

        config.refresh_from_db()
        self.assertEqual(config.value, '99')

    def test_initialize_updates_metadata_only(self) -> None:
        """
        Change a setting's declared description and check that initialization updates it without resetting
        the value.
        """
        updated_definitions = [
            SettingDefinition(
                key=item.key,
                description='Updated description' if str(item.key) == 'platform.pagination_size' else item.description,
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

        config = GlobalConfig.objects.get(pk='platform.pagination_size')
        self.assertEqual(config.description, 'Updated description')
        self.assertEqual(config.value, '25')

    def test_initialize_does_not_schedule_per_row_refresh(self) -> None:
        """
        Verify that synchronization suppresses per-row cache callbacks in favor of one full refresh.
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
        Verify that synchronization replaces the declared choice options when is_always_update is enabled.
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
                    if str(item.key) == 'platform.theme'
                    else item.variables
                ),
                is_always_update=item.is_always_update,
            )
            for item in TEST_DEFINITIONS
        ]
        with override_settings(GLOBAL_CONFIG_DEFINITIONS=updated_definitions):
            GlobalConfigInitializationService().initialize()

        config = GlobalConfig.objects.get(pk='platform.theme')
        self.assertEqual(config.variables, {'Dark': 'dark', 'Light': 'light', 'System': 'system'})

    def test_initialize_rejects_unknown_numeric_category(self) -> None:
        """
        Expect initialization to reject a setting whose numeric category ID has no active definition.
        """
        definition = SettingDefinition(
            key='platform.reports_enabled',
            description='Reports',
            default_value=False,
            value_type=TEST_DEFINITIONS[0].value_type,
            category_id=9,
        )
        with override_settings(GLOBAL_CONFIG_DEFINITIONS=[definition]), self.assertRaisesRegex(KeyError, 'id=9'):
            GlobalConfigInitializationService().initialize()

    def test_new_numeric_category_is_created_from_definitions(self) -> None:
        """
        Add a category definition and verify that initialization creates its numeric row.
        """
        extra_categories = [*TEST_CATEGORIES, CategoryDefinition(id=9, code='reports', name='Reports')]
        with override_settings(GLOBAL_CONFIG_CATEGORIES=extra_categories):
            GlobalConfigInitializationService().initialize()
            category = GlobalConfigCategory.objects.get(pk=9)
            self.assertEqual(category.code, 'reports')
            self.assertEqual(category.name, 'Reports')
