from django_gc.services import GlobalConfigService

try:
    from celery import shared_task
except ImportError:

    def refresh_global_configs_cache() -> int:
        """
        Принудительно обновить полный снимок GlobalConfig в кэше.
        """
        return GlobalConfigService().refresh_cache()
else:

    @shared_task(name='django_gc.refresh_global_configs_cache')
    def refresh_global_configs_cache() -> int:
        """
        Принудительно обновить полный снимок GlobalConfig в кэше.
        """
        return GlobalConfigService().refresh_cache()
