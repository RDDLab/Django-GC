import logging
from enum import StrEnum

from django_gc.services import GlobalConfigService

logger = logging.getLogger(__name__)


def refresh_global_config_value_safely(changed_key: str | StrEnum) -> None:
    """
    Refresh the changed setting after the database transaction commits.

    Log failures without raising them back to the caller because the write has already been committed.
    """
    try:
        GlobalConfigService().refresh_value(key=changed_key)
    except Exception as e:
        logger.exception(
            {'message': 'Failed to refresh changed GlobalConfig value after commit.', 'data': {'error': str(e)}}
        )


def refresh_global_configs_cache_safely() -> None:
    """
    Rebuild the full cache snapshot after a successful database commit.

    Log cache failures without propagating them to the operation that already saved the data.
    """
    try:
        GlobalConfigService().refresh_cache()
    except Exception as e:
        logger.exception({'message': 'Failed to refresh GlobalConfig cache after commit.', 'data': {'error': str(e)}})
