from typing import Any


class GlobalConfigError(Exception):
    """
    Базовая ошибка глобальной конфигурации.
    """


class GlobalConfigNotFoundError(GlobalConfigError):
    """
    Значение конфигурации отсутствует даже после полного обновления кэша.
    """

    def __init__(self, key: str) -> None:
        super().__init__(f'GlobalConfig с ключом <{key}> не найден.')
        self.key = key


class GlobalConfigValueError(GlobalConfigError):
    """
    Значение конфигурации отсутствует или не соответствует объявленному типу.
    """

    def __init__(self, key: str, value_type: Any | None = None) -> None:
        message = f'GlobalConfig с ключом <{key}> содержит некорректное значение.'
        if value_type is not None:
            message = f'{message} Тип: <{value_type}>.'
        super().__init__(message)
        self.key = key
        self.value_type = value_type


class GlobalConfigParseError(GlobalConfigValueError):
    """
    Сырое значение GlobalConfig невозможно преобразовать к объявленному типу.
    """


class GlobalConfigSnapshotIncompleteError(GlobalConfigError):
    """
    В БД отсутствует часть системных ключей полного снимка GlobalConfig.
    """

    def __init__(self, missing_keys: set[str]) -> None:
        sorted_keys = sorted(missing_keys)
        super().__init__(
            f'Невозможно сформировать полный снимок GlobalConfig. Отсутствуют ключи: <{", ".join(sorted_keys)}>.'
        )
        self.missing_keys = missing_keys


class GlobalConfigRefreshLockTimeoutError(GlobalConfigError):
    """
    Полный снимок нельзя безопасно обновить за время ожидания lock.
    """

    def __init__(self) -> None:
        super().__init__('Истекло время ожидания блокировки обновления GlobalConfig.')


class GlobalConfigCreationForbiddenError(GlobalConfigError):
    """
    Ключ GlobalConfig можно создать только через проектные definitions.
    """


class GlobalConfigDeletionForbiddenError(GlobalConfigError):
    """
    Созданный ключ GlobalConfig нельзя удалить.
    """


class GlobalConfigLockNotOwnedError(GlobalConfigError):
    """
    Публикация снимка запрещена после потери владения refresh lock.
    """
