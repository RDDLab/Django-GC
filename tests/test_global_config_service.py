from django.core.cache import cache
from django.db import connection
from django.test import TestCase

from django_gc.dto import GlobalConfigCacheValueDTO
from django_gc.enums import SettingType
from django_gc.exceptions import (
    GlobalConfigLockNotOwnedError,
    GlobalConfigNotFoundError,
    GlobalConfigParseError,
    GlobalConfigRefreshLockTimeoutError,
    GlobalConfigSnapshotIncompleteError,
)
from django_gc.models import GlobalConfig
from django_gc.services import GlobalConfigService
from tests.crypto import encrypt_text
from tests.definitions import TEST_DEFINITIONS
from tests.fakes import FakeCacheBackend, FakeLock

PAGINATION_KEY = 'platform-pagination-size'
SECRET_KEY = 'secret-token'


class GlobalConfigServiceTestCase(TestCase):
    """
    Проверять согласованную публикацию и чтение снимка GlobalConfig.
    """

    def setUp(self) -> None:
        cache.clear()
        self.service = GlobalConfigService()
        self._original_cache = self.service._cache

    def tearDown(self) -> None:
        self.service._cache = self._original_cache
        cache.clear()

    def create_service(
        self, *, backend: FakeCacheBackend | None = None
    ) -> tuple[GlobalConfigService, FakeCacheBackend]:
        """
        Создать штатный сервис с детерминированным fake cache.
        """
        backend = backend or FakeCacheBackend()
        self.service._cache = backend
        return self.service, backend

    def complete_snapshot(self) -> dict[str, object]:
        """
        Построить полный типизированный снимок всех системных ключей.
        """
        values: dict[str, object] = {GlobalConfigService.SNAPSHOT_READY_CACHE_KEY: True}
        values.update(
            {
                self.service.build_cache_key(key=item.key): GlobalConfigCacheValueDTO(
                    value=None, value_type=SettingType.STRING
                )
                for item in TEST_DEFINITIONS
            }
        )
        return values

    def test_cache_hit_does_not_read_database(self) -> None:
        """
        Вернуть типизированное значение из кэша без захвата refresh lock.
        """
        key = self.service.build_cache_key(key=PAGINATION_KEY)
        backend = FakeCacheBackend({key: GlobalConfigCacheValueDTO(value=42, value_type=SettingType.INTEGER)})
        service, _ = self.create_service(backend=backend)

        value = service.get_value(key=PAGINATION_KEY)

        self.assertEqual(value, 42)
        self.assertEqual(backend.lock.acquire_count, 0)

    def test_cache_miss_refreshes_all_values_and_retries(self) -> None:
        """
        При cache miss опубликовать снимок и повторить чтение ключа.
        """
        GlobalConfig.objects.filter(pk=PAGINATION_KEY).update(value='42')
        service, backend = self.create_service()

        value = service.get_value(key=PAGINATION_KEY)

        self.assertEqual(value, 42)
        self.assertEqual(backend.lock.acquire_count, 1)
        self.assertEqual(backend.lock.release_count, 1)

    def test_missing_value_after_refresh_raises_custom_error(self) -> None:
        """
        Вернуть доменную ошибку, если ключ отсутствует после полного refresh.
        """
        service, _ = self.create_service()

        with self.assertRaises(GlobalConfigNotFoundError):
            service.get_value(key='missing-config-key')

    def test_refresh_publishes_every_typed_key(self) -> None:
        """
        Опубликовать типизированные значения и маркер готовности одним снимком.
        """
        GlobalConfig.objects.filter(pk=PAGINATION_KEY).update(value='25')
        GlobalConfig.objects.filter(pk='maintenance-enabled').update(value='True')
        service, backend = self.create_service()

        refreshed_count = service.refresh_cache()

        self.assertEqual(refreshed_count, GlobalConfig.objects.count())
        self.assertEqual(backend.values['global-config:platform-pagination-size'].value, 25)
        self.assertIs(backend.values['global-config:snapshot-ready'], True)

    def test_secure_value_stays_encrypted_in_cache(self) -> None:
        """
        Не сохранять расшифрованное SECURE-значение в кэше.
        """
        GlobalConfig.objects.filter(pk=SECRET_KEY).update(value='encrypted-secret')
        service, backend = self.create_service()

        service.refresh_cache()

        cached_value = backend.values['global-config:secret-token']
        self.assertEqual(cached_value.value, 'encrypted-secret')
        self.assertEqual(cached_value.value_type, SettingType.SECURE)

    def test_secure_value_is_decrypted_only_on_read(self) -> None:
        """
        Расшифровать SECURE-значение только при выдаче вызывающему коду.
        """
        cache_key = self.service.build_cache_key(key=SECRET_KEY)
        encrypted_value = encrypt_text('plain-secret')
        service, _ = self.create_service(
            backend=FakeCacheBackend(
                {cache_key: GlobalConfigCacheValueDTO(value=encrypted_value, value_type=SettingType.SECURE)}
            )
        )

        value = service.get_value(key=SECRET_KEY)

        self.assertEqual(value, 'plain-secret')

    def test_legacy_plain_cache_value_forces_full_refresh(self) -> None:
        """
        Считать устаревший нетипизированный формат cache miss.
        """
        key = self.service.build_cache_key(key=PAGINATION_KEY)
        GlobalConfig.objects.filter(pk=PAGINATION_KEY).update(value='42')
        service, backend = self.create_service(backend=FakeCacheBackend({key: 'legacy-plain-value'}))

        value = service.get_value(key=PAGINATION_KEY)

        self.assertEqual(value, 42)
        self.assertEqual(backend.lock.acquire_count, 1)

    def test_nullable_none_is_a_valid_cached_result(self) -> None:
        """
        Вернуть None для nullable-настройки через публичный cache-aside путь.
        """
        GlobalConfig.objects.filter(pk='optional-note').update(value=None, nullable=True)
        service, _ = self.create_service()

        self.assertIsNone(service.get_value(key='optional-note'))

    def test_invalid_value_stops_full_refresh(self) -> None:
        """
        Не публиковать частичный снимок при ошибке преобразования значения.
        """
        GlobalConfig.objects.filter(pk=PAGINATION_KEY).update(value='not-an-integer')
        service, backend = self.create_service()

        with self.assertRaises(GlobalConfigParseError):
            service.refresh_cache()

        self.assertEqual(backend.mset_calls, [])

    def test_waiting_reader_skips_database_refresh_after_snapshot_publish(self) -> None:
        """
        Не читать БД повторно после публикации снимка другим владельцем lock.
        """
        key = self.service.build_cache_key(key=PAGINATION_KEY)
        lock = FakeLock()
        snapshot = self.complete_snapshot()
        snapshot[key] = GlobalConfigCacheValueDTO(value=25, value_type=SettingType.INTEGER)
        backend = FakeCacheBackend(snapshot, lock=lock)
        service, _ = self.create_service(backend=backend)

        refreshed_count = service.refresh_cache(requested_cache_key=key)

        self.assertEqual(refreshed_count, 0)
        self.assertEqual(backend.mset_calls, [])
        self.assertEqual(lock.release_count, 1)

    def test_expired_owner_does_not_publish_snapshot(self) -> None:
        """
        Запретить публикацию после потери владения refresh lock.
        """
        lock = FakeLock(lose_ownership_before_publish=True)
        backend = FakeCacheBackend(lock=lock)
        service, _ = self.create_service(backend=backend)

        with self.assertRaises(GlobalConfigLockNotOwnedError):
            service.refresh_cache()

        self.assertEqual(backend.mset_calls, [])
        self.assertEqual(lock.release_count, 0)

    def test_lock_timeout_does_not_publish_without_lock(self) -> None:
        """
        Завершить refresh ошибкой при timeout и отсутствии готового снимка.
        """
        lock = FakeLock(is_acquired=False)
        backend = FakeCacheBackend(lock=lock)
        service, _ = self.create_service(backend=backend)

        with self.assertRaises(GlobalConfigRefreshLockTimeoutError):
            service.refresh_cache()

        self.assertEqual(backend.mset_calls, [])
        self.assertEqual(lock.release_count, 0)

    def test_lock_timeout_accepts_snapshot_published_by_owner(self) -> None:
        """
        Принять готовый снимок после timeout ожидания владельца lock.
        """
        key = self.service.build_cache_key(key=PAGINATION_KEY)
        lock = FakeLock(is_acquired=False)
        snapshot = self.complete_snapshot()
        snapshot[key] = GlobalConfigCacheValueDTO(value=25, value_type=SettingType.INTEGER)
        backend = FakeCacheBackend(snapshot, lock=lock)
        service, _ = self.create_service(backend=backend)

        refreshed_count = service.refresh_cache(requested_cache_key=key)

        self.assertEqual(refreshed_count, 0)
        self.assertEqual(backend.mset_calls, [])

    def test_readiness_requires_marker_and_every_config_key(self) -> None:
        """
        Считать снимок готовым только при наличии маркера и всех ключей.
        """
        backend = FakeCacheBackend(self.complete_snapshot())
        service, _ = self.create_service(backend=backend)

        self.assertTrue(service.is_cache_ready())
        expected_keys = [
            self.service.build_cache_key(key=item.key)
            for item in sorted(TEST_DEFINITIONS, key=lambda item: str(item.key))
        ]
        self.assertEqual(backend.get_many_calls, [expected_keys])

    def test_readiness_fails_without_snapshot_marker(self) -> None:
        """
        Не считать набор значений готовым без маркера снимка.
        """
        service, backend = self.create_service()

        self.assertFalse(service.is_cache_ready())
        self.assertEqual(backend.get_many_calls, [])

    def test_missing_database_key_stops_snapshot_publication(self) -> None:
        """
        Остановить публикацию при повреждённом полном наборе ключей в БД.
        """
        table_name = GlobalConfig._meta.db_table
        with connection.cursor() as cursor:
            cursor.execute(f'DELETE FROM "{table_name}" WHERE "key" = %s', [PAGINATION_KEY])
        service, backend = self.create_service()

        with self.assertRaises(GlobalConfigSnapshotIncompleteError):
            service.refresh_cache()

        self.assertEqual(backend.mset_calls, [])
