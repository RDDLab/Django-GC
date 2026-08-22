from typing import Any

from django_gc.dto import CategoryDefinition, SettingDefinition
from django_gc.enums import SettingType
from django_gc.exceptions import (
    GlobalConfigCreationForbiddenError,
    GlobalConfigDeletionForbiddenError,
    GlobalConfigError,
    GlobalConfigLockNotOwnedError,
    GlobalConfigNotFoundError,
    GlobalConfigParseError,
    GlobalConfigRefreshLockTimeoutError,
    GlobalConfigSnapshotIncompleteError,
    GlobalConfigValueError,
)

__all__ = [
    'CategoryDefinition',
    'GlobalConfigCreationForbiddenError',
    'GlobalConfigDeletionForbiddenError',
    'GlobalConfigError',
    'GlobalConfigLockNotOwnedError',
    'GlobalConfigNotFoundError',
    'GlobalConfigParseError',
    'GlobalConfigRefreshLockTimeoutError',
    'GlobalConfigSnapshotIncompleteError',
    'GlobalConfigValueError',
    'SettingDefinition',
    'SettingType',
    'get_value',
    'is_cache_ready',
    'refresh_cache',
    'set_value',
]


def __getattr__(name: str) -> Any:
    """
    Лениво отдать runtime API после загрузки Django apps.
    """
    if name in {'get_value', 'is_cache_ready', 'refresh_cache', 'set_value'}:
        from django_gc import services

        return getattr(services, name)
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
