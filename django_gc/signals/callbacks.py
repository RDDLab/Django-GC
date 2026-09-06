import logging
from enum import StrEnum

from django_gc.services import GlobalConfigService

logger = logging.getLogger(__name__)


def refresh_global_config_value_safely(changed_key: str | StrEnum) -> None:
    """
    Обновить изменённый ключ после commit, не маскируя сохранённое изменение.
    """
    try:
        GlobalConfigService().refresh_value(key=changed_key)
    except Exception as e:
        logger.exception(
            {'message': 'Failed to refresh changed GlobalConfig value after commit.', 'data': {'error': str(e)}}
        )


def refresh_global_configs_cache_safely() -> None:
    """
    Полностью обновить кэш после commit, не маскируя уже сохранённое изменение.
    """
    try:
        GlobalConfigService().refresh_cache()
    except Exception as e:
        logger.exception({'message': 'Failed to refresh GlobalConfig cache after commit.', 'data': {'error': str(e)}})
