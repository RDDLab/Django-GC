from dataclasses import dataclass
from typing import Any

from django_gc.enums import SettingType


@dataclass(frozen=True)
class GlobalConfigCacheValueDTO:
    """
    Pair a cached setting value with its declared type.

    A SECURE entry retains its stored representation, which is ciphertext when encryption is configured.
    Runtime reads resolve it after cache lookup.
    """

    value: Any
    value_type: SettingType
