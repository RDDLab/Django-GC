from django_gc.services import GlobalConfigService

try:
    from celery import shared_task
except ImportError:

    def refresh_global_configs_cache() -> int:
        """
        Rebuild the full GlobalConfig snapshot and return the number of settings written.

        Register the operation as django_gc.refresh_global_configs_cache for Celery workers.
        """
        return GlobalConfigService().refresh_cache()
else:

    @shared_task(name='django_gc.refresh_global_configs_cache')
    def refresh_global_configs_cache() -> int:
        """
        Rebuild the full GlobalConfig snapshot and return the number of settings written.

        Expose a callable refresh entry point when Celery is unavailable.
        """
        return GlobalConfigService().refresh_cache()
