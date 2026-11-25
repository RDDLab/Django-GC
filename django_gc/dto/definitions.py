from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from django_gc.enums import SettingType


@dataclass(frozen=True)
class CategoryDefinition:
    """
    Declare the numeric ID, stable code and display name for a settings category.

    Initialization stores the ID. The admin resolves the code and name from the active definition.
    """

    id: int
    code: str
    name: str


@dataclass(frozen=True)
class SettingDefinition:
    """
    Declare a runtime key, its default value, type, category and editor metadata.

    Use previous_keys to identify eligible source rows when initializing a missing canonical key. Existing
    values take precedence over defaults and aliases.
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

    previous_keys: list[str] = field(default_factory=list)
