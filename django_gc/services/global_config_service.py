import ast
import json
import logging
import uuid
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
from django_gc.services.cache import CacheBackend, CacheLock
from django_gc.singleton import Singleton
from django_gc.utils import is_bool

_CACHE_MISS = object()
logger = logging.getLogger(__name__)


class GlobalConfigService(Singleton):
    """
    Предоставлять единый доступ к типизированным GlobalConfig через кэш.
    """

    CACHE_KEY_TEMPLATE = 'global-config:{key}'
    SNAPSHOT_READY_CACHE_KEY = 'global-config:snapshot-ready'
    REFRESH_LOCK_CACHE_KEY = 'global-config:refresh-lock'
    REFRESH_LOCK_TIMEOUT_SECONDS = 30
    REFRESH_LOCK_BLOCKING_TIMEOUT_SECONDS = 35

    def __init__(self) -> None:
        if hasattr(self, '_cache'):
            return
        self._cache = CacheBackend(alias=get_cache_alias())

    def build_cache_key(self, key: str | StrEnum) -> str:
        """
        Построить изолированный ключ кэша одной глобальной настройки.
        """
        return self.CACHE_KEY_TEMPLATE.format(key=str(key))

    def get_value(self, key: str | StrEnum) -> Any:
        """
        Получить значение только из кэша, синхронно восстановив весь снимок при промахе.

        Если после полного обновления значение не появилось, выбрасывается
        GlobalConfigNotFoundError.
        """
        cache_key = self.build_cache_key(key=key)
        cached_value = self._get_cache_value(cache_key=cache_key)
        if isinstance(cached_value, GlobalConfigCacheValueDTO):
            return self._resolve_cache_value(key=str(key), cached_value=cached_value)

        self.refresh_cache(requested_cache_key=cache_key)

        cached_value = self._get_cache_value(cache_key=cache_key)
        if not isinstance(cached_value, GlobalConfigCacheValueDTO):
            raise GlobalConfigNotFoundError(key=str(key))
        return self._resolve_cache_value(key=str(key), cached_value=cached_value)

    def refresh_value(self, key: str | StrEnum) -> None:
        """
        Перечитать и опубликовать только изменённый ключ под общей refresh-блокировкой.
        """
        lock = self._cache.get_lock(key=self.REFRESH_LOCK_CACHE_KEY, timeout=self.REFRESH_LOCK_TIMEOUT_SECONDS)
        acquired = lock.acquire(blocking=True, blocking_timeout=self.REFRESH_LOCK_BLOCKING_TIMEOUT_SECONDS)
        if not acquired:
            raise GlobalConfigRefreshLockTimeoutError()

        cache_key = self.build_cache_key(key=key)
        try:
            self._cache.delete(key=cache_key)
            config = (
                GlobalConfig.objects.only('key', 'value', 'value_type', 'nullable')
                .filter(pk=str(key))
                .first()
            )
            if config is None:
                raise GlobalConfigNotFoundError(key=str(key))
            self._cache.set_many_if_lock_owned(
                values={
                    cache_key: GlobalConfigCacheValueDTO(
                        value=self._parse_value(config=config),
                        value_type=SettingType(config.value_type),
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
        Сформировать полный снимок под распределённой блокировкой.

        Для cache miss после ожидания блокировки повторно проверяется запрошенный
        ключ: если другой процесс уже опубликовал снимок, повторное чтение БД
        не выполняется.
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
        Принять опубликованный владельцем снимок либо завершить refresh ошибкой.
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
        Проверить полный снимок и наличие запрошенного типизированного ключа.
        """
        cached_value = self._get_cache_value(cache_key=requested_cache_key)
        if cached_value is _CACHE_MISS:
            return False
        return self.is_cache_ready()

    def _refresh_cache_locked(self, lock: CacheLock) -> int:
        """
        Преобразовать и опубликовать снимок только под принадлежащим lock.
        """
        configs: list[GlobalConfig] = list(GlobalConfig.objects.only('key', 'value', 'value_type', 'nullable').all())
        required_keys = get_required_setting_keys()
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
        Проверить полный снимок без чтения GlobalConfig из БД.
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
        Прочитать только актуальный защищённый формат cache entry.

        Значения старого формата могли содержать расшифрованный SECURE и
        поэтому считаются cache miss с обязательным полным refresh.
        """
        cached_value: Any = self._cache.get(key=cache_key, default=_CACHE_MISS)
        if not isinstance(cached_value, GlobalConfigCacheValueDTO):
            return _CACHE_MISS
        return cached_value

    @classmethod
    def _resolve_cache_value(cls, key: str, cached_value: GlobalConfigCacheValueDTO) -> Any:
        """
        Вернуть runtime-значение, расшифровывая SECURE только в памяти.
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
        Обновить существующее значение; создание новых ключей не поддерживается.
        """
        config: GlobalConfig | None = GlobalConfig.objects.select_for_update().filter(pk=str(key)).first()
        if config is None:
            raise GlobalConfigNotFoundError(key=str(key))

        config.value = value
        config.save(update_fields=['value', 'updated_at'])
        return config

    @classmethod
    def _parse_value(cls, config: GlobalConfig) -> Any:
        """
        Преобразовать сохранённое значение к типу, объявленному в конфигурации.
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
        Разобрать JSON. Python-литерал с одинарными кавычками — запасной путь.
        """
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return ast.literal_eval(value)
