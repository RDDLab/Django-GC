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

PAGINATION_KEY = 'platform.pagination_size'
SECRET_KEY = 'auth.secret_token'


class GlobalConfigServiceTestCase(TestCase):
    """
    Exercise typed reads and snapshot publication against a controlled cache and refresh lease.

    Cover cache misses, failed refreshes and another worker publishing while a reader waits.
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
        Supply a GlobalConfigService instance wired to the deterministic fake cache for one test.
        """
        backend = backend or FakeCacheBackend()
        self.service._cache = backend
        return self.service, backend

    def complete_snapshot(self) -> dict[str, object]:
        """
        Build the complete typed entry set and readiness marker used to simulate a successful publication.
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
        Verify that a typed cache hit returns immediately without a database query or refresh lease.
        """
        key = self.service.build_cache_key(key=PAGINATION_KEY)
        backend = FakeCacheBackend({key: GlobalConfigCacheValueDTO(value=42, value_type=SettingType.INTEGER)})
        service, _ = self.create_service(backend=backend)

        value = service.get_value(key=PAGINATION_KEY)

        self.assertEqual(value, 42)
        self.assertEqual(backend.lock.acquire_count, 0)

    def test_refresh_value_replaces_only_changed_cache_entry(self) -> None:
        """
        Verify that refreshing one setting replaces its entry while leaving the other settings untouched.
        """
        GlobalConfig.objects.filter(pk=PAGINATION_KEY).update(value='42')
        changed_key = self.service.build_cache_key(key=PAGINATION_KEY)
        other_key = self.service.build_cache_key(key='platform.maintenance_enabled')
        service, backend = self.create_service(
            backend=FakeCacheBackend(
                {
                    changed_key: GlobalConfigCacheValueDTO(value=25, value_type=SettingType.INTEGER),
                    other_key: GlobalConfigCacheValueDTO(value=True, value_type=SettingType.BOOLEAN),
                }
            )
        )

        service.refresh_value(key=PAGINATION_KEY)

        self.assertEqual(backend.values[changed_key].value, 42)
        self.assertIs(backend.values[other_key].value, True)
        self.assertEqual(backend.lock.acquire_count, 1)
        self.assertEqual(backend.lock.release_count, 1)
        self.assertEqual(len(backend.mset_calls), 1)
        self.assertEqual(set(backend.mset_calls[0]), {changed_key})

    def test_cache_miss_refreshes_all_values_and_retries(self) -> None:
        """
        Verify that a lookup rebuilds the full snapshot on a miss, then returns the requested typed entry.
        """
        GlobalConfig.objects.filter(pk=PAGINATION_KEY).update(value='42')
        service, backend = self.create_service()

        value = service.get_value(key=PAGINATION_KEY)

        self.assertEqual(value, 42)
        self.assertEqual(backend.lock.acquire_count, 1)
        self.assertEqual(backend.lock.release_count, 1)

    def test_missing_value_after_refresh_raises_custom_error(self) -> None:
        """
        Expect GlobalConfigNotFoundError when a requested key is still missing after the refresh attempt.
        """
        service, _ = self.create_service()

        with self.assertRaises(GlobalConfigNotFoundError):
            service.get_value(key='missing-config-key')

    def test_refresh_publishes_every_typed_key(self) -> None:
        """
        Verify that the refresh writes all typed entries and the readiness marker in the same cache batch.
        """
        GlobalConfig.objects.filter(pk=PAGINATION_KEY).update(value='25')
        GlobalConfig.objects.filter(pk='platform.maintenance_enabled').update(value='True')
        service, backend = self.create_service()

        refreshed_count = service.refresh_cache()

        self.assertEqual(refreshed_count, GlobalConfig.objects.count())
        self.assertEqual(backend.values['global-config:platform.pagination_size'].value, 25)
        self.assertIs(backend.values['global-config:snapshot-ready'], True)

    def test_secure_value_stays_encrypted_in_cache(self) -> None:
        """
        Verify that an encrypted secure value remains ciphertext in the published snapshot.
        """
        GlobalConfig.objects.filter(pk=SECRET_KEY).update(value='encrypted-secret')
        service, backend = self.create_service()

        service.refresh_cache()

        cached_value = backend.values['global-config:auth.secret_token']
        self.assertEqual(cached_value.value, 'encrypted-secret')
        self.assertEqual(cached_value.value_type, SettingType.SECURE)

    def test_secure_value_is_decrypted_only_on_read(self) -> None:
        """
        Verify that a typed read returns plaintext while its cached entry retains the original token.
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
        Put an untyped value in the cache and verify that reading it triggers a full refresh.
        """
        key = self.service.build_cache_key(key=PAGINATION_KEY)
        GlobalConfig.objects.filter(pk=PAGINATION_KEY).update(value='42')
        service, backend = self.create_service(backend=FakeCacheBackend({key: 'legacy-plain-value'}))

        value = service.get_value(key=PAGINATION_KEY)

        self.assertEqual(value, 42)
        self.assertEqual(backend.lock.acquire_count, 1)

    def test_nullable_none_is_a_valid_cached_result(self) -> None:
        """
        Verify that a typed entry containing None represents a valid cache hit for a nullable setting.
        """
        GlobalConfig.objects.filter(pk='platform.optional_note').update(value=None, nullable=True)
        service, _ = self.create_service()

        self.assertIsNone(service.get_value(key='platform.optional_note'))

    def test_invalid_value_stops_full_refresh(self) -> None:
        """
        Verify that a stored value that fails parsing prevents a partial snapshot from being published.
        """
        GlobalConfig.objects.filter(pk=PAGINATION_KEY).update(value='not-an-integer')
        service, backend = self.create_service()

        with self.assertRaises(GlobalConfigParseError):
            service.refresh_cache()

        self.assertEqual(backend.mset_calls, [])

    def test_waiting_reader_skips_database_refresh_after_snapshot_publish(self) -> None:
        """
        Simulate another worker publishing while a reader waits and verify that the reader reuses the
        snapshot.
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
        Simulate an expired lease and verify that the previous owner cannot publish the snapshot.
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
        Expect a refresh timeout error when the wait expires without a usable snapshot or a lease.
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
        Verify that a timed-out caller can use the complete snapshot written by the lease owner.
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
        Verify that a readiness marker is insufficient when an active setting is missing from the cache.
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
        Verify that the typed cache entries alone are insufficient to report a complete snapshot.
        """
        service, backend = self.create_service()

        self.assertFalse(service.is_cache_ready())
        self.assertEqual(backend.get_many_calls, [])

    def test_missing_database_key_stops_snapshot_publication(self) -> None:
        """
        Verify that a missing declared row raises the incomplete-snapshot error before any entries are
        published.
        """
        table_name = GlobalConfig._meta.db_table
        with connection.cursor() as cursor:
            cursor.execute(f'DELETE FROM "{table_name}" WHERE "key" = %s', [PAGINATION_KEY])
        service, backend = self.create_service()

        with self.assertRaises(GlobalConfigSnapshotIncompleteError):
            service.refresh_cache()

        self.assertEqual(backend.mset_calls, [])
