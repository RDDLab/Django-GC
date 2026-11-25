from functools import partial
from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase

from django_gc.models import GlobalConfig
from django_gc.services import GlobalConfigInitializationService, GlobalConfigService
from django_gc.services.cache import CacheBackend
from django_gc.signals.callbacks import refresh_global_config_value_safely, refresh_global_configs_cache_safely
from django_gc.signals.refresh_global_configs_cache import refresh_global_configs_cache


class GlobalConfigSignalsTestCase(TestCase):
    """
    Verify how saves and explicit initialization schedule cache work after a database commit.
    """

    def setUp(self) -> None:
        cache.clear()
        self.service = GlobalConfigService()
        self._original_cache = self.service._cache

    def tearDown(self) -> None:
        self.service._cache = self._original_cache
        cache.clear()

    def test_save_schedules_changed_value_refresh_after_commit(self) -> None:
        """
        Save a setting and verify that the post-commit callback refreshes only the changed key.
        """
        config = GlobalConfig.objects.get(pk='platform.pagination_size')
        config.value = '25'
        with self.captureOnCommitCallbacks() as callbacks:
            config.save(update_fields=['value', 'updated_at'])

        self.assertEqual(len(callbacks), 1)
        callback = callbacks[0]
        self.assertIsInstance(callback, partial)
        self.assertIs(callback.func, refresh_global_config_value_safely)
        self.assertEqual(callback.keywords, {'changed_key': str(config.key)})

    def test_fixture_load_does_not_refresh_cache(self) -> None:
        """
        Verify that a raw fixture save schedules no cache refresh callback.
        """
        config = GlobalConfig.objects.get(pk='platform.pagination_size')
        with self.captureOnCommitCallbacks() as callbacks:
            refresh_global_configs_cache(sender=GlobalConfig, instance=config, using='default', raw=True)

        self.assertEqual(callbacks, [])

    def test_initialization_schedules_safe_refresh_after_commit(self) -> None:
        """
        Verify that explicit initialization schedules the safe full refresh after commit.
        """
        with self.captureOnCommitCallbacks() as callbacks:
            GlobalConfigInitializationService().initialize()

        self.assertIn(refresh_global_configs_cache_safely, callbacks)

    def test_safe_refresh_does_not_propagate_cache_failure(self) -> None:
        """
        Simulate a failed post-commit cache refresh and verify that the exception is logged and contained.
        """

        with (
            patch.object(CacheBackend, 'is_shared', True),
            patch.object(self.service._cache, 'get_lock', side_effect=RuntimeError('cache unavailable')) as get_lock,
            self.assertLogs('django_gc.signals.callbacks', level='ERROR') as log_context
        ):
            refresh_global_configs_cache_safely()

        get_lock.assert_called_once()
        self.assertEqual(len(log_context.records), 1)
