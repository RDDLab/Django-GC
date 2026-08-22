from datetime import date, time
from decimal import Decimal
from uuid import UUID

from django.test import SimpleTestCase
from django.utils import timezone

from django_gc.enums import SettingType
from django_gc.models import GlobalConfig
from django_gc.services import GlobalConfigService


class SettingTypeChoicesTests(SimpleTestCase):
    """
    Проверить Django choices собственного ChoicesEnumMixin.
    """

    def test_builds_value_label_pairs(self) -> None:
        """
        Собрать choices из value и label() без IntegerChoices.
        """
        choices = [(value, str(label)) for value, label in SettingType.choices()]
        self.assertIn((0, 'String'), choices)
        self.assertIn((22, 'UUID'), choices)
        self.assertEqual(len(choices), len(SettingType))
        self.assertEqual(SettingType.STRING, 0)
        self.assertEqual(str(SettingType.STRING.label()), 'String')
        self.assertEqual(SettingType.values(), {member.value for member in SettingType})
        self.assertIn('String', SettingType.labels())
        self.assertIn('UUID', SettingType.labels())


class GlobalConfigTypeParseTests(SimpleTestCase):
    """
    Проверить преобразование каждого поддерживаемого SettingType.
    """

    def parse(self, value: str, value_type: SettingType) -> object:
        """
        Разобрать сырое значение без обращения к БД.
        """
        return GlobalConfigService._parse_value(
            config=GlobalConfig(key='typed-key', value=value, value_type=int(value_type), nullable=False)
        )

    def test_scalar_types(self) -> None:
        """
        Разобрать скалярные типы.
        """
        self.assertEqual(self.parse('hello', SettingType.STRING), 'hello')
        self.assertIs(self.parse('True', SettingType.BOOLEAN), True)
        self.assertIs(self.parse('0', SettingType.BOOLEAN), False)
        self.assertEqual(self.parse('1.5', SettingType.FLOAT), 1.5)
        self.assertEqual(self.parse('1.50', SettingType.DECIMAL), Decimal('1.50'))
        self.assertEqual(self.parse('12', SettingType.INTEGER), 12)
        self.assertEqual(self.parse('encrypted', SettingType.SECURE), 'encrypted')
        self.assertEqual(self.parse('21.08.2026', SettingType.DATE), date(2026, 8, 21))
        self.assertEqual(self.parse('13:45:00', SettingType.TIME), time(13, 45, 0))
        parsed_datetime = self.parse('21.08.2026 13:45:00', SettingType.DATETIME)
        self.assertTrue(timezone.is_aware(parsed_datetime))
        self.assertEqual(self.parse('abc', SettingType.STRING_CHOICES), 'abc')
        self.assertEqual(self.parse('3', SettingType.INTEGER_CHOICES), 3)
        self.assertEqual(self.parse('1.2', SettingType.FLOAT_CHOICES), 1.2)
        self.assertEqual(self.parse('1.2', SettingType.DECIMAL_CHOICES), Decimal('1.2'))
        self.assertEqual(
            self.parse('11111111-1111-1111-1111-111111111111', SettingType.UUID),
            UUID('11111111-1111-1111-1111-111111111111'),
        )

    def test_array_types(self) -> None:
        """
        Разобрать массивы с разделителем точка с запятой.
        """
        self.assertEqual(self.parse('a;b', SettingType.STRING_ARRAY), ['a', 'b'])
        self.assertEqual(self.parse('1;2', SettingType.INTEGER_ARRAY), [1, 2])
        self.assertEqual(self.parse('1.1;2.2', SettingType.FLOAT_ARRAY), [1.1, 2.2])
        self.assertEqual(self.parse('1.1;2.2', SettingType.DECIMAL_ARRAY), [Decimal('1.1'), Decimal('2.2')])

    def test_json_and_multiple_choices(self) -> None:
        """
        Разобрать JSON и множественный выбор.
        """
        self.assertEqual(self.parse('{"a": 1}', SettingType.JSON), {'a': 1})
        self.assertEqual(self.parse('[1, 2]', SettingType.INTEGER_MULTIPLE_CHOICES), [1, 2])
        self.assertEqual(self.parse('["a", "b"]', SettingType.STRING_MULTIPLE_CHOICES), ['a', 'b'])
        self.assertEqual(self.parse('[1.1, 2.2]', SettingType.FLOAT_MULTIPLE_CHOICES), [1.1, 2.2])
