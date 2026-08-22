from typing import Any

from django_gc.exceptions import GlobalConfigLockNotOwnedError
from django_gc.services.cache import CacheLock


class FakeLock:
    """
    Имитировать распределённую блокировку и потерю владения lease.
    """

    def __init__(self, is_acquired: bool = True, lose_ownership_before_publish: bool = False) -> None:
        self.is_acquired = is_acquired
        self.lose_ownership_before_publish = lose_ownership_before_publish
        self.is_owned = False
        self.acquire_count = 0
        self.release_count = 0
        self.token = 'fake-token'
        self.key = 'global-config:refresh-lock'
        self.timeout = 30

    def acquire(self, **_kwargs: object) -> bool:
        """
        Зафиксировать попытку приобретения и вернуть настроенный результат.
        """
        self.acquire_count += 1
        self.is_owned = self.is_acquired
        return self.is_acquired

    def still_owned(self) -> bool:
        """
        Проверить сохранённое fake-владение.
        """
        return self.is_owned

    def release(self) -> None:
        """
        Освободить принадлежащую fake-блокировку.
        """
        if not self.is_owned:
            raise GlobalConfigLockNotOwnedError()
        self.is_owned = False
        self.release_count += 1


class FakeCacheBackend:
    """
    Детерминированный cache backend для проверки снимка.
    """

    def __init__(self, values: dict[str, Any] | None = None, lock: FakeLock | None = None) -> None:
        self.values: dict[str, Any] = dict(values or {})
        self.lock = lock or FakeLock()
        self.get_calls: list[str] = []
        self.get_many_calls: list[list[str]] = []
        self.mset_calls: list[dict[str, Any]] = []

    def get(self, key: str, default: Any = None) -> Any:
        """
        Прочитать одно подготовленное значение.
        """
        self.get_calls.append(key)
        return self.values.get(key, default)

    def get_many(self, keys: list[str]) -> dict[str, Any]:
        """
        Прочитать подготовленные значения по списку ключей.
        """
        self.get_many_calls.append(keys)
        return {key: self.values[key] for key in keys if key in self.values}

    def set_many(self, values: dict[str, Any]) -> None:
        """
        Сохранить снимок в память.
        """
        self.mset_calls.append(values)
        self.values.update(values)

    def delete(self, key: str) -> None:
        """
        Удалить ключ из памяти.
        """
        self.values.pop(key, None)

    def get_lock(self, **_kwargs: object) -> FakeLock:
        """
        Вернуть подготовленную блокировку.
        """
        return self.lock

    def set_many_if_lock_owned(self, values: dict[str, Any], lock: FakeLock | CacheLock) -> None:
        """
        Записать снимок только при сохранении fake-владения.
        """
        fake_lock = lock
        if isinstance(fake_lock, FakeLock) and fake_lock.lose_ownership_before_publish:
            fake_lock.is_owned = False
        if not fake_lock.still_owned():
            raise GlobalConfigLockNotOwnedError()
        self.set_many(values=values)
