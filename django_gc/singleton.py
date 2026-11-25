from typing import ClassVar, Self


class Singleton:
    """
    Reuse a single instance per concrete class in the current process.
    """

    _instance: ClassVar['Singleton | None'] = None

    def __new__(cls, *args: object, **kwargs: object) -> Self:
        """
        Return the subclass's existing instance or allocate and remember one on first use.
        """
        instance = cls.__dict__.get('_instance')
        if instance is None:
            instance = super().__new__(cls)
            cls._instance = instance
        return instance
