from time import monotonic, sleep
from typing import Any
from uuid import uuid4

from django.core.cache import caches

from django_gc.exceptions import GlobalConfigLockNotOwnedError

_LOCK_POLL_SECONDS = 0.05


class CacheLock:
    """
    Блокировка на Django cache через атомарный add.
    """

    def __init__(self, cache: Any, key: str, timeout: int, token: str) -> None:
        self._cache = cache
        self.key = key
        self.timeout = timeout
        self.token = token
        self.is_owned = False

    def acquire(self, *, blocking: bool, blocking_timeout: float) -> bool:
        """
        Захватить lock, при необходимости ожидая освобождения.
        """
        deadline = monotonic() + blocking_timeout
        while True:
            if self._cache.add(self.key, self.token, self.timeout):
                self.is_owned = True
                return True
            if not blocking or monotonic() >= deadline:
                return False
            sleep(_LOCK_POLL_SECONDS)

    def still_owned(self) -> bool:
        """
        Проверить, что текущий token всё ещё владеет lock.
        """
        return self._cache.get(self.key) == self.token

    def release(self) -> None:
        """
        Освободить принадлежащую блокировку.
        """
        if not self.still_owned():
            raise GlobalConfigLockNotOwnedError()
        self._cache.delete(self.key)
        self.is_owned = False


class CacheBackend:
    """
    Обёртка над Django cache для снимка GlobalConfig.
    """

    def __init__(self, alias: str) -> None:
        self._cache = caches[alias]

    def get(self, key: str, default: Any = None) -> Any:
        """
        Прочитать одно значение.
        """
        return self._cache.get(key, default)

    def get_many(self, keys: list[str]) -> dict[str, Any]:
        """
        Прочитать несколько значений одним запросом.
        """
        return dict(self._cache.get_many(keys))

    def set_many(self, values: dict[str, Any]) -> None:
        """
        Опубликовать снимок без TTL.
        """
        self._cache.set_many(values, timeout=None)

    def delete(self, key: str) -> None:
        """
        Удалить ключ кэша.
        """
        self._cache.delete(key)

    def get_lock(self, key: str, timeout: int) -> CacheLock:
        """
        Создать блокировку на указанном ключе.
        """
        return CacheLock(cache=self._cache, key=key, timeout=timeout, token=uuid4().hex)

    def set_many_if_lock_owned(self, values: dict[str, Any], lock: CacheLock) -> None:
        """
        Записать снимок только пока процесс остаётся владельцем lock.
        """
        if not lock.still_owned():
            raise GlobalConfigLockNotOwnedError()
        self.set_many(values=values)
