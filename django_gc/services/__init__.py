from enum import StrEnum
from typing import Any

from django_gc.models import GlobalConfig
from django_gc.services.global_config_initialization_service import GlobalConfigInitializationService
from django_gc.services.global_config_service import GlobalConfigService

__all__ = [
    'GlobalConfigInitializationService',
    'GlobalConfigService',
    'get_value',
    'is_cache_ready',
    'refresh_cache',
    'set_value',
]


def get_value(key: str | StrEnum) -> Any:
    """
    Получить типизированное значение GlobalConfig.
    """
    return GlobalConfigService().get_value(key=key)


def set_value(key: str | StrEnum, value: Any) -> GlobalConfig:
    """
    Обновить существующее значение GlobalConfig.
    """
    return GlobalConfigService.set_value(key=key, value=value)


def refresh_cache() -> int:
    """
    Опубликовать полный снимок GlobalConfig.
    """
    return GlobalConfigService().refresh_cache()


def is_cache_ready() -> bool:
    """
    Проверить готовность полного снимка.
    """
    return GlobalConfigService().is_cache_ready()
