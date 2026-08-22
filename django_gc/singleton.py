from typing import Self


class Singleton:
    """
    Хранить один экземпляр класса на процесс.
    """

    def __new__(cls, *args: object, **kwargs: object) -> Self:
        """
        Вернуть уже созданный экземпляр класса, если он есть.
        """
        instance = cls.__dict__.get('_instance')
        if instance is None:
            instance = super().__new__(cls)
            cls._instance = instance
        return instance
