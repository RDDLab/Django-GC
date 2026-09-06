from functools import partial

from django.core.cache import cache
from django.test import TestCase

from django_gc.models import GlobalConfig
from django_gc.services import GlobalConfigInitializationService, GlobalConfigService
from django_gc.signals.callbacks import refresh_global_config_value_safely, refresh_global_configs_cache_safely
from django_gc.signals.refresh_global_configs_cache import refresh_global_configs_cache


class GlobalConfigSignalsTestCase(TestCase):
    """
    Проверить регистрацию точечного refresh после изменения GlobalConfig.
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
        Запланировать callback только после успешной фиксации изменения.
        """
        config = GlobalConfig.objects.get(pk='platform-pagination-size')
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
        Не запускать побочные эффекты при загрузке raw fixture.
        """
        config = GlobalConfig.objects.get(pk='platform-pagination-size')
        with self.captureOnCommitCallbacks() as callbacks:
            refresh_global_configs_cache(
                sender=GlobalConfig,
                instance=config,
                using='default',
                raw=True,
            )

        self.assertEqual(callbacks, [])

    def test_initialization_schedules_safe_refresh_after_commit(self) -> None:
        """
        Не завершать post-migrate ошибкой после уже зафиксированной БД.
        """
        with self.captureOnCommitCallbacks() as callbacks:
            GlobalConfigInitializationService().initialize()

        self.assertIn(refresh_global_configs_cache_safely, callbacks)

    def test_safe_refresh_does_not_propagate_cache_failure(self) -> None:
        """
        Залогировать отказ backend после commit без повторной ошибки операции.
        """

        class BrokenCache:
            def get_lock(self, **_kwargs: object) -> object:
                raise RuntimeError('cache unavailable')

        self.service._cache = BrokenCache()  # type: ignore[assignment]
        with self.assertLogs('django_gc.signals.callbacks', level='ERROR') as log_context:
            refresh_global_configs_cache_safely()

        self.assertEqual(len(log_context.records), 1)
