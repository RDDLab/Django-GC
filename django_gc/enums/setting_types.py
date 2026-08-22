from enum import IntEnum
from typing import override

from django.utils.functional import Promise
from django.utils.translation import gettext_lazy as _

from django_gc.enums.choices_enum import ChoicesEnumMixin


class SettingType(ChoicesEnumMixin, IntEnum):
    """
    Типы данных, использующиеся в глобальных конфигурациях.
    """

    STRING = 0
    BOOLEAN = 1
    FLOAT = 2
    DECIMAL = 3
    INTEGER = 4
    SECURE = 5
    DATE = 6
    TIME = 7
    DATETIME = 8
    STRING_ARRAY = 9
    INTEGER_ARRAY = 10
    FLOAT_ARRAY = 11
    DECIMAL_ARRAY = 12
    COLOR = 13
    STRING_CHOICES = 14
    INTEGER_CHOICES = 15
    FLOAT_CHOICES = 16
    DECIMAL_CHOICES = 17
    JSON = 18
    INTEGER_MULTIPLE_CHOICES = 19
    STRING_MULTIPLE_CHOICES = 20
    FLOAT_MULTIPLE_CHOICES = 21
    UUID = 22

    @override
    def label(self) -> Promise:
        """
        Вернуть переводимую подпись типа.
        """
        return {
            self.STRING: _('String'),
            self.BOOLEAN: _('Boolean'),
            self.FLOAT: _('Float'),
            self.DECIMAL: _('Decimal'),
            self.INTEGER: _('Integer'),
            self.SECURE: _('Secure'),
            self.DATE: _('Date'),
            self.TIME: _('Time'),
            self.DATETIME: _('DateTime'),
            self.STRING_ARRAY: _('String Array'),
            self.INTEGER_ARRAY: _('Integer Array'),
            self.FLOAT_ARRAY: _('Float Array'),
            self.DECIMAL_ARRAY: _('Decimal Array'),
            self.COLOR: _('Color'),
            self.STRING_CHOICES: _('String Choices'),
            self.INTEGER_CHOICES: _('Integer Choices'),
            self.FLOAT_CHOICES: _('Float Choices'),
            self.DECIMAL_CHOICES: _('Decimal Choices'),
            self.JSON: _('Json'),
            self.INTEGER_MULTIPLE_CHOICES: _('Integer Multiple Choices'),
            self.STRING_MULTIPLE_CHOICES: _('String Multiple Choices'),
            self.FLOAT_MULTIPLE_CHOICES: _('Float Multiple Choices'),
            self.UUID: _('UUID'),
        }[self]
