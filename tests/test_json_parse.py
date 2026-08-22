from django.test import SimpleTestCase

from django_gc.enums import SettingType
from django_gc.models import GlobalConfig
from django_gc.services import GlobalConfigService


class GlobalConfigJsonParseTests(SimpleTestCase):
    """
    JSON GlobalConfig не ломается подменой кавычек внутри строк.
    """

    def test_json_with_apostrophe_in_string_is_parsed(self) -> None:
        """
        Сохранить валидный JSON, где в значении есть апостроф.
        """
        config = GlobalConfig(
            key='test-json-apostrophe',
            value='{"note": "it\'s valid"}',
            value_type=int(SettingType.JSON),
            nullable=False,
        )

        self.assertEqual(GlobalConfigService._parse_value(config=config), {'note': "it's valid"})

    def test_python_literal_json_fallback_is_parsed(self) -> None:
        """
        Принять Python-литерал с одинарными кавычками как запасной формат.
        """
        config = GlobalConfig(
            key='test-json-literal', value="{'enabled': True}", value_type=int(SettingType.JSON), nullable=False
        )

        self.assertEqual(GlobalConfigService._parse_value(config=config), {'enabled': True})
