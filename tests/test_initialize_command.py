from io import StringIO
from unittest.mock import patch

from django.apps import apps
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db.models.signals import post_migrate
from django.test import TestCase, override_settings
from django.utils.translation import override

from django_gc import ProviderDefinition, get_value
from django_gc.management.commands.initialize_global_configs import Command
from django_gc.models import GlobalConfig, GlobalConfigCategory


class InitializeGlobalConfigsCommandTestCase(TestCase):
    """
    Verify that explicit initialization can seed settings before dependent Django checks run.

    Cover repeat execution, missing schema and the absence of initialization on post_migrate.
    """

    def test_help_uses_the_active_language(self) -> None:
        """
        Build a command parser in each supported locale after importing the command.

        Verify that its description follows the active language even when the command class has already been loaded.
        """
        command = Command()
        expected_descriptions = {
            'en': 'Initialize project and provider settings while preserving existing values.',
            'ru': 'Инициализировать настройки проекта и подключённых библиотек с сохранением существующих значений.',
        }
        for language, description in expected_descriptions.items():
            with self.subTest(language=language), override(language):
                parser = command.create_parser('manage.py', 'initialize_global_configs')
                self.assertEqual(parser.description, description)

    @override_settings(GLOBAL_CONFIG_PROVIDERS=[ProviderDefinition(
        provider='tests.provider.ExampleProvider', category_ids={'general': 30}
    )])
    def test_initializes_provider_and_preserves_existing_values_on_repeat(self) -> None:
        """
        Initialize a provider through the command and then edit both project and provider settings.

        Run the command again and verify that both working values are preserved.
        """
        GlobalConfig.objects.filter(pk='platform.pagination_size').update(value='99')
        call_command('initialize_global_configs', stdout=StringIO())
        self.assertEqual(get_value('example.limit', use_cache=False), 7)
        GlobalConfig.objects.filter(pk='example.limit').update(value='8')

        call_command('initialize_global_configs', stdout=StringIO())

        self.assertEqual(get_value('example.limit', use_cache=False), 8)
        self.assertEqual(get_value('platform.pagination_size', use_cache=False), 99)

    def test_initialization_does_not_run_checks_that_depend_on_missing_keys(self) -> None:
        """
        Explicitly enable normal checks at invocation and verify that this command still skips them.
        """
        with patch.object(Command, 'check', side_effect=AssertionError('Dependent check ran.')) as check:
            Command(stdout=StringIO()).execute(skip_checks=False, force_color=False, no_color=False)
        check.assert_not_called()

    def test_missing_tables_require_schema_migration(self) -> None:
        """
        Simulate missing tables and verify that the command raises an error with the migration instructions.
        """
        with (
            patch('django_gc.management.commands.initialize_global_configs.table_exists', return_value=False),
            self.assertRaisesRegex(CommandError, 'migrate --skip-checks'),
        ):
            call_command('initialize_global_configs', stdout=StringIO())

    @override_settings(GLOBAL_CONFIG_PROVIDERS=[ProviderDefinition(
        provider='tests.provider.ExampleProvider', category_ids={'general': 30}
    )])
    def test_post_migrate_does_not_create_categories_or_keys(self) -> None:
        """
        Send post_migrate and verify that new provider keys and categories appear only after the command
        runs.
        """
        config = apps.get_app_config('django_gc')
        post_migrate.send(
            sender=config, app_config=config, using='default', verbosity=0, interactive=False, apps=apps
        )
        self.assertFalse(GlobalConfigCategory.objects.filter(pk=30).exists())
        self.assertFalse(GlobalConfig.objects.filter(pk='example.limit').exists())
        call_command('initialize_global_configs', stdout=StringIO())
        self.assertTrue(GlobalConfigCategory.objects.filter(pk=30).exists())
        self.assertTrue(GlobalConfig.objects.filter(pk='example.limit').exists())
