import ast
import json
import logging
import uuid
from collections.abc import Sequence
from datetime import date, datetime, time
from decimal import Decimal
from enum import StrEnum
from typing import Any

from django.db import transaction
from django.utils import timezone

from django_gc.conf import decrypt_value, get_cache_alias, get_required_setting_keys
from django_gc.dto import GlobalConfigCacheValueDTO
from django_gc.enums import SettingType
from django_gc.exceptions import (
    GlobalConfigLockNotOwnedError,
    GlobalConfigNotFoundError,
    GlobalConfigParseError,
    GlobalConfigRefreshLockTimeoutError,
    GlobalConfigSnapshotIncompleteError,
    GlobalConfigValueError,
)
from django_gc.models import GlobalConfig
from django_gc.registry import resolve_key
from django_gc.services.cache import CacheBackend, CacheLock
from django_gc.singleton import Singleton
from django_gc.utils import is_bool

_CACHE_MISS = object()
logger = logging.getLogger(__name__)


class GlobalConfigService(Singleton):
    """
    Read and write typed GlobalConfig values and coordinate publication of the cache snapshot.

    Runtime reads use the cache by default. The database remains the source of truth for snapshot rebuilds
    and explicit fresh reads.
    """

    CACHE_KEY_TEMPLATE = 'global-config:{key}'
    SNAPSHOT_READY_CACHE_KEY = 'global-config:snapshot-ready'
    REFRESH_LOCK_CACHE_KEY = 'global-config:refresh-lock'
    REFRESH_LOCK_TIMEOUT_SECONDS = 30
    REFRESH_LOCK_BLOCKING_TIMEOUT_SECONDS = 35

    def __init__(self) -> None:
        cache: CacheBackend | None = getattr(self, '_cache', None)
        self._cache = cache if cache is not None else CacheBackend(alias=get_cache_alias())

    def build_cache_key(self, key: str | StrEnum) -> str:
        """
        Build the per-setting cache key after resolving any declared alias to its canonical name.
        """
        return self.CACHE_KEY_TEMPLATE.format(key=resolve_key(key=str(key)))

    def get_value(self, key: str | StrEnum, *, use_cache: bool = True) -> Any:
        """
        Return the typed value for a canonical key or a declared alias.

        Bypass the cache with use_cache=False. Otherwise, rebuild the snapshot synchronously on a miss and
        retry the lookup. Raise GlobalConfigNotFoundError if the setting is still unavailable.
        """
        key = resolve_key(key=str(key))
        if not use_cache:
            config = GlobalConfig.objects.filter(pk=str(key)).first()
            if config is None:
                raise GlobalConfigNotFoundError(key=str(key))
            parsed = self._parse_value(config=config)
            return self._resolve_cache_value(
                key=str(key),
                cached_value=GlobalConfigCacheValueDTO(value=parsed, value_type=SettingType(config.value_type))
            )
        cache_key = self.build_cache_key(key=key)
        cached_value = self._get_cache_value(cache_key=cache_key)
        if isinstance(cached_value, GlobalConfigCacheValueDTO):
            return self._resolve_cache_value(key=str(key), cached_value=cached_value)

        self.refresh_cache(requested_cache_key=cache_key)

        cached_value = self._get_cache_value(cache_key=cache_key)
        if not isinstance(cached_value, GlobalConfigCacheValueDTO):
            raise GlobalConfigNotFoundError(key=str(key))
        return self._resolve_cache_value(key=str(key), cached_value=cached_value)

    def get_values(self, *, keys: Sequence[str], use_cache: bool = True) -> dict[str, Any]:
        """
        Return typed values keyed by the supplied names, including any aliases.

        With use_cache=False, fetch all canonical rows in a single query in the caller's database
        transaction. Raise GlobalConfigNotFoundError when a requested row is missing.
        """
        if use_cache:
            return {key: self.get_value(key=key) for key in keys}
        canonical_keys = {key: resolve_key(key=key) for key in keys}
        configs = GlobalConfig.objects.filter(pk__in=canonical_keys.values())
        values = {
            config.key: self._resolve_cache_value(
                key=config.key,
                cached_value=GlobalConfigCacheValueDTO(value=self._parse_value(config=config),
                                                       value_type=SettingType(config.value_type))
            ) for config in configs
        }
        missing = set(canonical_keys.values()).difference(values)
        if missing:
            raise GlobalConfigNotFoundError(key=sorted(missing)[0])
        return {key: values[canonical] for key, canonical in canonical_keys.items()}

    def refresh_value(self, key: str | StrEnum) -> None:
        """
        Refresh the cache entry for a single setting under the shared refresh lock.

        Invalidate the old entry before reading the row and publish the parsed replacement after checking
        lock ownership.
        """
        key = resolve_key(key=str(key))
        lock = self._cache.get_lock(key=self.REFRESH_LOCK_CACHE_KEY, timeout=self.REFRESH_LOCK_TIMEOUT_SECONDS)
        acquired = lock.acquire(blocking=True, blocking_timeout=self.REFRESH_LOCK_BLOCKING_TIMEOUT_SECONDS)
        if not acquired:
            raise GlobalConfigRefreshLockTimeoutError()

        cache_key = self.build_cache_key(key=key)
        try:
            self._cache.delete(key=cache_key)
            config = GlobalConfig.objects.only('key', 'value', 'value_type', 'nullable').filter(pk=str(key)).first()
            if config is None:
                raise GlobalConfigNotFoundError(key=str(key))
            self._cache.set_many_if_lock_owned(
                values={
                    cache_key: GlobalConfigCacheValueDTO(
                        value=self._parse_value(config=config), value_type=SettingType(config.value_type)
                    )
                },
                lock=lock,
            )
        finally:
            try:
                lock.release()
            except GlobalConfigLockNotOwnedError:
                logger.warning({'message': 'GlobalConfig refresh lock expired before release.', 'data': {}})

    def refresh_cache(self, requested_cache_key: str | None = None) -> int:
        """
        Rebuild the full cache snapshot under the refresh lock and return the number of settings written.

        When requested_cache_key is supplied, reuse a complete snapshot containing that entry if another
        worker publishes it while this call waits. Reusing a snapshot returns zero.
        """
        lock = self._cache.get_lock(key=self.REFRESH_LOCK_CACHE_KEY, timeout=self.REFRESH_LOCK_TIMEOUT_SECONDS)
        acquired = lock.acquire(blocking=True, blocking_timeout=self.REFRESH_LOCK_BLOCKING_TIMEOUT_SECONDS)
        if not acquired:
            return self._handle_refresh_lock_timeout(requested_cache_key=requested_cache_key)

        try:
            if requested_cache_key is not None and self._is_requested_snapshot_available(
                requested_cache_key=requested_cache_key
            ):
                return 0
            return self._refresh_cache_locked(lock=lock)
        finally:
            try:
                lock.release()
            except GlobalConfigLockNotOwnedError:
                logger.warning({'message': 'GlobalConfig refresh lock expired before release.', 'data': {}})

    def _handle_refresh_lock_timeout(self, requested_cache_key: str | None) -> int:
        """
        Return zero when an acceptable snapshot is available after a lock wait times out.

        When a caller requested a specific cache key, require that entry as well. Raise
        GlobalConfigRefreshLockTimeoutError if the required snapshot is unavailable.
        """
        logger.warning({'message': 'GlobalConfig refresh lock wait timed out.', 'data': {}})
        if requested_cache_key is None and self.is_cache_ready():
            return 0
        if requested_cache_key is not None and self._is_requested_snapshot_available(
            requested_cache_key=requested_cache_key
        ):
            return 0
        raise GlobalConfigRefreshLockTimeoutError()

    def _is_requested_snapshot_available(self, requested_cache_key: str) -> bool:
        """
        Check that the requested entry uses the current typed format and that the full snapshot is ready.
        """
        cached_value = self._get_cache_value(cache_key=requested_cache_key)
        if cached_value is _CACHE_MISS:
            return False
        return self.is_cache_ready()

    def _refresh_cache_locked(self, lock: CacheLock) -> int:
        """
        Read and parse every active setting before publishing the entries and readiness marker.

        Raise GlobalConfigSnapshotIncompleteError for missing declared rows and verify lock ownership before
        writing.
        """
        required_keys = get_required_setting_keys()
        configs: list[GlobalConfig] = list(
            GlobalConfig.objects.only('key', 'value', 'value_type', 'nullable').filter(pk__in=required_keys)
        )
        config_keys = {str(config.key) for config in configs}
        missing_keys = required_keys - config_keys
        if missing_keys:
            raise GlobalConfigSnapshotIncompleteError(missing_keys=missing_keys)

        values: dict[str, Any] = {
            self.build_cache_key(key=config.key): GlobalConfigCacheValueDTO(
                value=self._parse_value(config=config), value_type=SettingType(config.value_type)
            )
            for config in configs
        }
        values[self.SNAPSHOT_READY_CACHE_KEY] = True
        self._cache.set_many_if_lock_owned(values=values, lock=lock)
        return len(configs)

    def is_cache_ready(self) -> bool:
        """
        Require the readiness marker and a typed cache entry for every active definition.

        Check the cache and the code-defined catalog without querying the settings tables.
        """
        marker = self._cache.get(key=self.SNAPSHOT_READY_CACHE_KEY, default=False)
        if marker is not True:
            return False

        cache_keys = [self.build_cache_key(key=key) for key in sorted(get_required_setting_keys())]
        cached_values = self._cache.get_many(keys=cache_keys)
        return len(cached_values) == len(cache_keys) and all(
            isinstance(value, GlobalConfigCacheValueDTO) for value in cached_values.values()
        )

    def _get_cache_value(self, cache_key: str) -> GlobalConfigCacheValueDTO | object:
        """
        Read an entry only if it uses the current typed format.

        Treat legacy entries as misses because their representation may contain a decrypted secret.
        """
        cached_value: Any = self._cache.get(key=cache_key, default=_CACHE_MISS)
        if not isinstance(cached_value, GlobalConfigCacheValueDTO):
            return _CACHE_MISS
        return cached_value

    @classmethod
    def _resolve_cache_value(cls, key: str, cached_value: GlobalConfigCacheValueDTO) -> Any:
        """
        Return the runtime value from a typed cache entry.

        Resolve secure values in memory on read and raise GlobalConfigParseError if the stored value cannot
        be decrypted.
        """
        if cached_value.value_type != SettingType.SECURE:
            return cached_value.value
        if cached_value.value is None:
            return None

        decrypted_value = decrypt_value(text=str(cached_value.value))
        if decrypted_value is None:
            raise GlobalConfigParseError(key=key, value_type=cached_value.value_type)
        return decrypted_value

    @classmethod
    @transaction.atomic
    def set_value(cls, key: str | StrEnum, value: Any) -> GlobalConfig:
        """
        Write a storage-format value to an existing setting and return its model.

        Resolve aliases and lock the target row before saving. Raise GlobalConfigNotFoundError if the row
        has not been initialized.
        """
        key = resolve_key(key=str(key))
        config: GlobalConfig | None = GlobalConfig.objects.select_for_update().filter(pk=str(key)).first()
        if config is None:
            raise GlobalConfigNotFoundError(key=str(key))

        config.value = value
        config.save(update_fields=['value', 'updated_at'])
        return config

    @classmethod
    def lock_values(cls, *, keys: list[str]) -> None:
        """
        Lock existing setting rows by canonical primary key in stable order.

        Call this inside the caller's transaction. Raise GlobalConfigNotFoundError if any requested setting
        is absent.
        """
        keys = [resolve_key(key=key) for key in keys]
        locked_keys = set(
            GlobalConfig.objects.select_for_update().filter(pk__in=keys).order_by('pk').values_list('pk', flat=True)
        )
        missing = set(keys).difference(locked_keys)
        if missing:
            raise GlobalConfigNotFoundError(key=sorted(missing)[0])

    @classmethod
    @transaction.atomic
    def set_typed_value(cls, *, key: str | StrEnum, value: Any) -> GlobalConfig:
        """
        Validate and serialize a Python value before saving it to an existing setting.

        Resolve aliases, lock the row and apply the owning provider's rules inside the transaction. Return
        the updated model after checking that the serialized value can be parsed.
        """
        from django_gc.registry import validate_change

        key = resolve_key(key=str(key))
        config = GlobalConfig.objects.select_for_update().filter(pk=str(key)).first()
        if config is None:
            raise GlobalConfigNotFoundError(key=str(key))
        normalized = validate_change(key=str(key), value=value)
        value_type = SettingType(config.value_type)
        if value_type == SettingType.JSON:
            stored = json.dumps(normalized)
        elif value_type in {SettingType.STRING_ARRAY, SettingType.INTEGER_ARRAY,
                            SettingType.FLOAT_ARRAY, SettingType.DECIMAL_ARRAY}:
            stored = ';'.join(str(item) for item in normalized)
        elif normalized is None:
            stored = None
        else:
            stored = str(normalized)
        config.value = stored
        cls._parse_value(config=config)
        config.save(update_fields=['value', 'updated_at'])
        return config

    @classmethod
    def parse_value(cls, *, config: GlobalConfig) -> Any:
        """
        Parse a model's stored value according to its declared type without consulting the cache.

        Secure values retain their stored representation. Runtime reads perform decryption separately.
        """
        return cls._parse_value(config=config)

    @classmethod
    def _parse_value(cls, config: GlobalConfig) -> Any:
        """
        Convert the stored representation into the type declared on the setting row.

        Return None for an empty nullable setting. Raise GlobalConfigValueError for an empty required value
        and GlobalConfigParseError when conversion fails.
        """
        if config.value is None or config.value == '':
            if config.nullable:
                return None
            raise GlobalConfigValueError(key=config.key, value_type=config.value_type)

        try:
            value = config.value
            value_type = SettingType(config.value_type)
            match value_type:
                case SettingType.STRING:
                    return value
                case SettingType.SECURE:
                    return value
                case SettingType.BOOLEAN:
                    return is_bool(value)
                case SettingType.INTEGER:
                    return int(value)
                case SettingType.FLOAT:
                    return float(value)
                case SettingType.DECIMAL:
                    return Decimal(value)
                case SettingType.DATE:
                    return date.fromisoformat('-'.join(reversed(value.split('.'))))
                case SettingType.TIME:
                    return time.fromisoformat(value)
                case SettingType.DATETIME:
                    naive_value = datetime.strptime(value, '%d.%m.%Y %H:%M:%S')
                    return timezone.make_aware(naive_value)
                case SettingType.INTEGER_ARRAY:
                    return list(map(int, value.split(';'))) if value else list[int]()
                case SettingType.STRING_ARRAY:
                    return list(map(str, value.split(';'))) if value else list[str]()
                case SettingType.FLOAT_ARRAY:
                    return list(map(float, value.split(';'))) if value else list[float]()
                case SettingType.DECIMAL_ARRAY:
                    return list(map(Decimal, value.split(';'))) if value else list[Decimal]()
                case SettingType.STRING_CHOICES:
                    return str(value)
                case SettingType.INTEGER_CHOICES:
                    return int(value)
                case SettingType.FLOAT_CHOICES:
                    return float(value)
                case SettingType.DECIMAL_CHOICES:
                    return Decimal(value)
                case SettingType.JSON:
                    return cls._parse_json_like(value=value)
                case SettingType.INTEGER_MULTIPLE_CHOICES | SettingType.FLOAT_MULTIPLE_CHOICES:
                    return json.loads(value)
                case SettingType.STRING_MULTIPLE_CHOICES:
                    return cls._parse_json_like(value=value)
                case SettingType.UUID:
                    return uuid.UUID(value)
                case _:
                    raise GlobalConfigValueError(key=config.key, value_type=value_type)
        except GlobalConfigValueError:
            raise
        except (TypeError, ValueError, SyntaxError, json.JSONDecodeError) as e:
            raise GlobalConfigParseError(key=config.key, value_type=config.value_type) from e

    @classmethod
    def _parse_json_like(cls, value: str) -> Any:
        """
        Parse JSON, falling back to Python literal syntax for previously stored values.

        Let an invalid literal raise so the caller can report the setting and its type.
        """
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return ast.literal_eval(value)
