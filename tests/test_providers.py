from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.test import TestCase, override_settings

from django_gc import CategoryDefinition, ProviderDefinition, get_value, set_typed_value, set_value
from django_gc.conf import get_category_definitions, get_setting_definitions
from django_gc.forms import GlobalConfigForm
from django_gc.models import GlobalConfig
from django_gc.registry import authorize_changes, get_provider
from django_gc.services import GlobalConfigInitializationService

REGISTRATION = ProviderDefinition(provider='tests.provider.ExampleProvider', category_ids={'general': 30})


@override_settings(GLOBAL_CONFIG_PROVIDERS=[REGISTRATION])
class ConfigurationProvidersTestCase(TestCase):
    """
    Verify how registered providers join the shared catalog and protect writes using their own rules.
    """

    def setUp(self) -> None:
        GlobalConfigInitializationService().initialize()

    def test_collects_project_and_library_definitions(self) -> None:
        """
        Check that the configured provider contributes its namespaced keys and uses the category ID assigned
        by the project.
        """
        self.assertIn('example.limit', {str(item.key) for item in get_setting_definitions()})
        category = next(item for item in get_category_definitions() if item.id == 30)
        self.assertEqual(category.code, 'example.general')
        self.assertIsNotNone(get_provider(key='example.limit'))
        self.assertIsNone(get_provider(key='example.unknown'))

    def test_rejects_category_collisions(self) -> None:
        """
        Reject a provider category that uses a numeric ID already assigned by the project.
        """
        with (
            override_settings(GLOBAL_CONFIG_CATEGORIES=[CategoryDefinition(id=30, code='project', name='Project')]),
            self.assertRaises(ImproperlyConfigured),
        ):
            get_setting_definitions()

    def test_rejects_incomplete_category_mapping(self) -> None:
        """
        Report a configuration error when the registration does not assign all of the provider's category
        codes.
        """
        with override_settings(GLOBAL_CONFIG_PROVIDERS=[ProviderDefinition(
            provider='tests.provider.ExampleProvider', category_ids={}
        )]), self.assertRaises(ImproperlyConfigured):
            get_category_definitions()

    def test_preserves_imported_and_live_values(self) -> None:
        """
        Verify that provider initialization supplies the first value and preserves a later authorized
        update.
        """
        self.assertEqual(get_value('example.limit', use_cache=False), 7)
        with authorize_changes(keys=['example.limit']):
            set_typed_value(key='example.limit', value=9)
        GlobalConfigInitializationService().initialize()
        self.assertEqual(get_value('example.limit', use_cache=False), 9)

    def test_protected_writes_require_owner_authorization(self) -> None:
        """
        Verify that the two public update functions and a direct model save reject unauthorized protected
        writes.
        """
        with self.assertRaises(PermissionDenied):
            set_value('example.limit', '8')
        with self.assertRaises(PermissionDenied):
            set_typed_value(key='example.limit', value=8)
        config = GlobalConfig.objects.get(pk='example.limit')
        config.value = '8'
        with self.assertRaises(PermissionDenied):
            config.save(update_fields=['value'])
        self.assertEqual(get_value('example.limit', use_cache=False), 7)

    def test_authorization_is_scoped_and_validated(self) -> None:
        """
        Check that authorization applies only to the selected key and does not bypass provider validation.
        """
        with authorize_changes(keys=['example.limit']):
            with self.assertRaises(ValueError):
                set_typed_value(key='example.limit', value=11)
            with self.assertRaises(PermissionDenied):
                set_typed_value(key='example.origins', value=['https://example.test'])
        with self.assertRaises(PermissionDenied):
            set_typed_value(key='example.limit', value=8)

    def test_json_lists_round_trip_and_empty_list_is_valid_form_value(self) -> None:
        """
        Round-trip a provider-owned JSON list and verify that the standard form also accepts an empty list.
        """
        with authorize_changes(keys=['example.origins']):
            set_typed_value(key='example.origins', value=['https://example.test'])
        self.assertEqual(get_value('example.origins', use_cache=False), ['https://example.test'])
        config = GlobalConfig.objects.get(pk='example.origins')
        form = GlobalConfigForm(data={'value': '[]'}, instance=config)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.typed_value(), [])
