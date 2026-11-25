from enum import StrEnum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from django_gc.models import GlobalConfig


def get_value(key: str | StrEnum, *, use_cache: bool = True) -> Any:
    """
    Return the typed value of a setting identified by its current key or a declared alias.

    Use a shared cache by default and refresh its snapshot on a miss. Read the database directly when a local
    or dummy backend is configured or use_cache is False. Missing or invalid values raise GlobalConfigError.
    """
    from django_gc.services.global_config_service import GlobalConfigService

    return GlobalConfigService().get_value(key=key, use_cache=use_cache)


def set_value(key: str | StrEnum, value: Any) -> 'GlobalConfig':
    """
    Write a storage-format value to an existing setting and return the updated model.

    The key may be current or a declared alias. Use set_typed_value when the caller has a Python value that
    still needs serialization.
    """
    from django_gc.services.global_config_service import GlobalConfigService

    return GlobalConfigService.set_value(key=key, value=value)


def refresh_cache() -> int:
    """
    Rebuild the cache snapshot from the declared settings and return the number of entries written.

    An incomplete or invalid snapshot raises an error before publication. Return zero when a different
    worker has already published an acceptable snapshot or when there is no shared cache to refresh.
    """
    from django_gc.services.global_config_service import GlobalConfigService

    return GlobalConfigService().refresh_cache()


def is_cache_ready() -> bool:
    """
    Check the cache marker and all typed entries required by the current definitions.

    Return False without a shared cache. This check never queries the settings tables.
    """
    from django_gc.services.global_config_service import GlobalConfigService

    return GlobalConfigService().is_cache_ready()


def set_typed_value(*, key: str | StrEnum, value: Any) -> 'GlobalConfig':
    """
    Validate and serialize a Python value for an existing setting.

    Accept a current key or a declared alias, apply the owning provider's validation and return the updated
    model. Protected settings require authorization from their owner.
    """
    from django_gc.services.global_config_service import GlobalConfigService

    return GlobalConfigService.set_typed_value(key=key, value=value)
