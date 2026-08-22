import logging

from django_gc.services import GlobalConfigService

logger = logging.getLogger(__name__)


def refresh_global_configs_cache_safely() -> None:
    """
    Полностью обновить кэш после commit, не маскируя уже сохранённое изменение.
    """
    try:
        GlobalConfigService().refresh_cache()
    except Exception as e:
        logger.exception({'message': 'Failed to refresh GlobalConfig cache after commit.', 'data': {'error': str(e)}})
