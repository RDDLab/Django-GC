from django.test import SimpleTestCase

from django_gc.enums import SettingType
from django_gc.models import GlobalConfig
from django_gc.services import GlobalConfigService


class GlobalConfigJsonParseTests(SimpleTestCase):
    """
    Verify strict JSON parsing and the fallback for older values stored using Python literal syntax.
    """

    def test_json_with_apostrophe_in_string_is_parsed(self) -> None:
        """
        Parse JSON containing an apostrophe and verify that the string is returned unchanged.
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
        Verify that a Python literal with single quotes still loads when strict JSON decoding fails.
        """
        config = GlobalConfig(
            key='test-json-literal', value="{'enabled': True}", value_type=int(SettingType.JSON), nullable=False
        )

        self.assertEqual(GlobalConfigService._parse_value(config=config), {'enabled': True})
