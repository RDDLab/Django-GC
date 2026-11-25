from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase, override_settings

from django_gc import get_value, is_cache_ready, refresh_cache, set_typed_value
from django_gc.dto import GlobalConfigCacheValueDTO
from django_gc.enums import SettingType
from django_gc.services import GlobalConfigService
from django_gc.services.cache import CacheBackend
from django_gc.tasks import refresh_global_configs_cache

PAGINATION_KEY = 'platform.pagination_size'
SECRET_KEY = 'auth.secret_token'


class DatabaseReadsTestCase(TestCase):
    """
    Exercise the runtime API when there is no shared cache for settings.
    """

    def test_backends_without_shared_storage_read_current_values(self) -> None:
        """
        Bypass both local and dummy backends even if a stale snapshot exists.

        Verify that batch reads need one query and snapshot operations do not access the database.
        """
        original = get_value(PAGINATION_KEY, use_cache=False)
        service = GlobalConfigService()
        for backend_path in (
            'django.core.cache.backends.locmem.LocMemCache',
            'django.core.cache.backends.dummy.DummyCache'
        ):
            caches = {'default': {'BACKEND': backend_path, 'LOCATION': 'gc-without-shared-cache'}}
            with self.subTest(backend=backend_path), override_settings(CACHES=caches), patch.object(
                service, '_cache', CacheBackend(alias='default')
            ):
                set_typed_value(key=PAGINATION_KEY, value=original)
                cache.set(service.build_cache_key(key=PAGINATION_KEY), GlobalConfigCacheValueDTO(
                    value=999, value_type=SettingType.INTEGER
                ))
                cache.set(service.SNAPSHOT_READY_CACHE_KEY, True)

                self.assertEqual(get_value(PAGINATION_KEY), original)
                set_typed_value(key=PAGINATION_KEY, value=original + 1)
                self.assertEqual(get_value(PAGINATION_KEY), original + 1)

                with self.assertNumQueries(1):
                    self.assertEqual(service.get_values(keys=[PAGINATION_KEY, SECRET_KEY]), {
                        PAGINATION_KEY: original + 1,
                        SECRET_KEY: 'secret'
                    })
                with self.assertNumQueries(0):
                    self.assertFalse(is_cache_ready())
                    self.assertEqual(refresh_cache(), 0)
                    self.assertEqual(refresh_global_configs_cache(), 0)
                    service.refresh_value(key=PAGINATION_KEY)
