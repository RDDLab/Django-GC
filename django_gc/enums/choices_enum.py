from enum import Enum

from django.utils.functional import Promise


class ChoicesEnumMixin(Enum):
    """
    Дать Django choices из членов enum с методом ``label()``.
    """

    def label(self) -> Promise:
        """
        Вернуть человекочитаемую подпись члена enum.
        """
        raise NotImplementedError

    @classmethod
    def values(cls) -> set[object]:
        """
        Вернуть множество значений членов.
        """
        return {item.value for item in cls}

    @classmethod
    def labels(cls) -> set[str]:
        """
        Вернуть множество строковых подписей членов.
        """
        return {str(item.label()) for item in cls}

    @classmethod
    def choices(cls) -> list[tuple[object, Promise]]:
        """
        Вернуть пары value/label для поля Django.
        """
        return [(member.value, member.label()) for member in cls]
