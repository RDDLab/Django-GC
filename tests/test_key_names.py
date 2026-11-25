from dataclasses import replace

from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.test import SimpleTestCase, TestCase, override_settings

from django_gc import get_value, set_value
from django_gc.conf import get_setting_definitions
from django_gc.dto import GlobalConfigCacheValueDTO
from django_gc.enums import SettingType
from django_gc.models import GlobalConfig
from django_gc.registry import authorize_changes
from django_gc.services import GlobalConfigInitializationService, GlobalConfigService
from tests.definitions import TEST_DEFINITIONS


class KeyNamesTestCase(SimpleTestCase):
    """
    Check the canonical key format and alias uniqueness without querying the database.
    """

    def test_rejects_noncanonical_new_names(self) -> None:
        """
        Reject new keys containing uppercase letters, hyphens or additional namespace segments.
        """
        for key in ['SCOPE.value', 'scope.VALUE', 'scope.some-value', 'value', 'scope.sub.value']:
            with self.subTest(key=key), override_settings(
                GLOBAL_CONFIG_DEFINITIONS=[replace(TEST_DEFINITIONS[0], key=key)]
            ), self.assertRaises(ImproperlyConfigured):
                get_setting_definitions()

    def test_rejects_ambiguous_alias(self) -> None:
        """
        Reject definitions that assign the same previous key to two canonical settings.
        """
        definitions = [replace(item, previous_keys=['old-key']) for item in TEST_DEFINITIONS[:2]]
        with override_settings(GLOBAL_CONFIG_DEFINITIONS=definitions), self.assertRaises(ImproperlyConfigured):
            get_setting_definitions()

    def test_alias_cannot_shadow_active_key(self) -> None:
        """
        Reject an alias that would hide another setting's active canonical key.
        """
        definitions = [replace(TEST_DEFINITIONS[0], previous_keys=[str(TEST_DEFINITIONS[1].key)]),
                       TEST_DEFINITIONS[1]]
        with override_settings(GLOBAL_CONFIG_DEFINITIONS=definitions), self.assertRaises(ImproperlyConfigured):
            get_setting_definitions()


class PreviousKeysTestCase(TestCase):
    """
    Verify that explicit initialization can reuse old rows and resolve old names to active settings.

    Exercise cache lookups, encrypted values, conflicting old rows and provider protections.
    """

    def test_initialization_preserves_value_and_old_cache_cannot_override_current_value(self) -> None:
        """
        Copy a previous value into the missing canonical row and verify that an old cache entry cannot
        override it.
        """
        definition = replace(TEST_DEFINITIONS[0], key='platform.page_size',
                             previous_keys=['platform.pagination_size'])
        definitions = [definition, *TEST_DEFINITIONS[1:]]
        GlobalConfig.objects.filter(pk='platform.pagination_size').update(value='99')
        cache.set('global-config:platform.pagination_size',
                  GlobalConfigCacheValueDTO(value=3, value_type=SettingType.INTEGER))
        with override_settings(GLOBAL_CONFIG_DEFINITIONS=definitions):
            GlobalConfigInitializationService().initialize()
            self.assertEqual(get_value('platform.pagination_size', use_cache=False), 99)
            set_value('platform.pagination_size', '80')
            GlobalConfigService().refresh_cache()
            self.assertEqual(get_value('platform.page_size'), 80)
            self.assertEqual(get_value('platform.pagination_size'), 80)
            values = GlobalConfigService().get_values(
                keys=['platform.page_size', 'platform.pagination_size'], use_cache=False
            )
            self.assertEqual(set(values.values()), {80})
            GlobalConfigInitializationService().initialize()
            self.assertEqual(get_value('platform.page_size', use_cache=False), 80)
            GlobalConfig.objects.filter(pk='platform.pagination_size').update(value='retired invalid value')
            self.assertEqual(GlobalConfigService().refresh_cache(), len(definitions))
            self.assertEqual(get_value('platform.pagination_size'), 80)
        GlobalConfig.objects.filter(pk='platform.pagination_size').update(value='99')
        self.assertEqual(GlobalConfig.objects.get(pk='platform.pagination_size').value, '99')

    def test_secure_value_is_copied_without_double_encryption(self) -> None:
        """
        Verify that initialization copies ciphertext unchanged and the new key resolves to the original
        secret.
        """
        previous = GlobalConfig.objects.get(pk='auth.secret_token')
        definitions = [replace(item, key='auth.api_secret', previous_keys=['auth.secret_token'])
                       if item.key == 'auth.secret_token' else item for item in TEST_DEFINITIONS]
        with override_settings(GLOBAL_CONFIG_DEFINITIONS=definitions):
            GlobalConfigInitializationService().initialize()
            self.assertEqual(GlobalConfig.objects.get(pk='auth.api_secret').value, previous.value)
            self.assertEqual(get_value('auth.api_secret', use_cache=False), 'secret')

    @override_settings(GLOBAL_CONFIG_PROVIDERS=[])
    def test_conflicting_previous_values_abort_initialization(self) -> None:
        """
        Verify that conflicting previous rows abort the transaction instead of picking an arbitrary value.
        """
        definition = replace(TEST_DEFINITIONS[0], key='platform.limit',
                             previous_keys=['platform.pagination_size', 'legacy.page_size'])
        previous = GlobalConfig.objects.get(pk='platform.pagination_size')
        previous.pk = 'legacy.page_size'
        previous.value = '90'
        GlobalConfig.objects.bulk_create([previous])
        with (
            override_settings(GLOBAL_CONFIG_DEFINITIONS=[definition, *TEST_DEFINITIONS[1:]]),
            self.assertRaises(ValueError),
        ):
            GlobalConfigInitializationService().initialize()
        self.assertFalse(GlobalConfig.objects.filter(pk='platform.limit').exists())

    def test_alias_keeps_owner_protection(self) -> None:
        """
        Verify that writing through an alias still requires authorization from the provider that owns the
        key.
        """
        from django_gc import ProviderDefinition

        registration = ProviderDefinition(provider='tests.provider.ExampleProvider', category_ids={'general': 30})
        with override_settings(GLOBAL_CONFIG_PROVIDERS=[registration]):
            GlobalConfigInitializationService().initialize()
            with self.assertRaises(PermissionDenied):
                set_value('example.LEGACY_LIMIT', '8')
            with authorize_changes(keys=['example.LEGACY_LIMIT']):
                set_value('example.LEGACY_LIMIT', '8')
            self.assertEqual(get_value('example.limit', use_cache=False), 8)
