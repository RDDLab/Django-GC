from dataclasses import dataclass
from typing import Any

from django_gc.enums import SettingType


@dataclass(frozen=True)
class GlobalConfigCacheValueDTO:
    """
    Типизированное значение снимка GlobalConfig.

    Для SettingType.SECURE поле value содержит только зашифрованное значение.
    """

    value: Any
    value_type: SettingType
