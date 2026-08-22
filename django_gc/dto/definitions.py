from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from django_gc.enums import SettingType


@dataclass(frozen=True)
class CategoryDefinition:
    """
    Описать системную категорию GlobalConfig для инициализации.
    """

    id: int
    code: str
    name: str


@dataclass(frozen=True)
class SettingDefinition:
    """
    Описать управляемый кодом ключ GlobalConfig для инициализации.
    """

    key: str | StrEnum
    description: str
    default_value: Any
    value_type: SettingType
    category_id: int
    nullable: bool = False
    is_read_only: bool = False
    variables: dict[str, Any] | None = None
    is_always_update: bool = False
