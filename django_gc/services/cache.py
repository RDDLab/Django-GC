from time import monotonic, sleep
from typing import Any
from uuid import uuid4

from django.core.cache import caches

from django_gc.exceptions import GlobalConfigLockNotOwnedError

_LOCK_POLL_SECONDS = 0.05


class CacheLock:
    """
    Represent an expiring refresh lease in Django's cache.

    Acquire the lease with an atomic cache add and use a unique token to check current ownership.
    """

    def __init__(self, cache: Any, key: str, timeout: int, token: str) -> None:
        """
        Create a lease for a cache key with a separate owner token and expiry in seconds.
        """
        self._cache = cache
        self.key = key
        self.timeout = timeout
        self.token = token
        self.is_owned = False

    def acquire(self, *, blocking: bool, blocking_timeout: float) -> bool:
        """
        Attempt to add the lease and return whether it was acquired.

        When blocking is enabled, retry until blocking_timeout elapses. The lease itself uses the separate
        timeout supplied at creation.
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
        Check whether the token currently stored under the lease key matches this lock's token.
        """
        return self._cache.get(self.key) == self.token

    def release(self) -> None:
        """
        Remove the lease after verifying current ownership.

        Raise GlobalConfigLockNotOwnedError if the lease has expired or its owner has changed.
        """
        if not self.still_owned():
            raise GlobalConfigLockNotOwnedError()
        self._cache.delete(self.key)
        self.is_owned = False


class CacheBackend:
    """
    Wrap the configured Django cache for typed snapshot entries and refresh leases.
    """

    def __init__(self, alias: str) -> None:
        """
        Bind cache operations to the Django backend registered under alias.
        """
        self._cache = caches[alias]

    def get(self, key: str, default: Any = None) -> Any:
        """
        Read a cache key or return the supplied default when it is absent.
        """
        return self._cache.get(key, default)

    def get_many(self, keys: list[str]) -> dict[str, Any]:
        """
        Fetch all present entries for a list of keys in one cache backend call.
        """
        return dict(self._cache.get_many(keys))

    def set_many(self, values: dict[str, Any]) -> None:
        """
        Write the supplied cache entries without an expiry.
        """
        self._cache.set_many(values, timeout=None)

    def delete(self, key: str) -> None:
        """
        Remove the given cache key if present.
        """
        self._cache.delete(key)

    def get_lock(self, key: str, timeout: int) -> CacheLock:
        """
        Create a lease with a unique owner token and the given timeout, without acquiring it.
        """
        return CacheLock(cache=self._cache, key=key, timeout=timeout, token=uuid4().hex)

    def set_many_if_lock_owned(self, values: dict[str, Any], lock: CacheLock) -> None:
        """
        Write cache entries after checking that the supplied lock still owns its lease.

        Raise GlobalConfigLockNotOwnedError if the ownership check fails.
        """
        if not lock.still_owned():
            raise GlobalConfigLockNotOwnedError()
        self.set_many(values=values)
