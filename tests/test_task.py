from django.core.cache import cache
from django.test import TestCase

from django_gc.models import GlobalConfig
from django_gc.services import GlobalConfigService
from django_gc.tasks import refresh_global_configs_cache


class GlobalConfigTaskTestCase(TestCase):
    """
    Проверить, что задача вызывает полный refresh.
    """

    def setUp(self) -> None:
        cache.clear()

    def tearDown(self) -> None:
        cache.clear()

    def test_task_refreshes_snapshot(self) -> None:
        """
        Опубликовать снимок через task-функцию.
        """
        GlobalConfig.objects.filter(pk='platform-pagination-size').update(value='33')
        refreshed_count = refresh_global_configs_cache()
        self.assertEqual(refreshed_count, GlobalConfig.objects.count())
        self.assertTrue(GlobalConfigService().is_cache_ready())
        self.assertEqual(GlobalConfigService().get_value(key='platform-pagination-size'), 33)
