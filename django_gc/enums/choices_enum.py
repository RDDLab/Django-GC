from enum import Enum

from django.utils.functional import Promise


class ChoicesEnumMixin(Enum):
    """
    Build Django-compatible choices from enum members that provide a translatable label.
    """

    def label(self) -> Promise:
        """
        Return an individual member's lazy display label. Subclasses supply the label for each member.
        """
        raise NotImplementedError

    @classmethod
    def values(cls) -> set[object]:
        """
        Return all enum values as an unordered set for membership checks.
        """
        return {item.value for item in cls}

    @classmethod
    def labels(cls) -> set[str]:
        """
        Resolve display labels in the active language and return them as an unordered set.
        """
        return {str(item.label()) for item in cls}

    @classmethod
    def choices(cls) -> list[tuple[object, Promise]]:
        """
        Return each enum value and lazy label in declaration order for use in a Django field.
        """
        return [(member.value, member.label()) for member in cls]
