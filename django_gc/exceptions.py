from typing import Any

from django.utils.translation import gettext as _


class GlobalConfigError(Exception):
    """
    Base exception for configuration lookup, validation and cache publication failures.
    """


class GlobalConfigNotFoundError(GlobalConfigError):
    """
    Report a missing setting and expose its key for the caller.

    A cache-backed lookup can raise this after a snapshot refresh. A direct lookup or update can raise it
    when the row is absent.
    """

    def __init__(self, key: str) -> None:
        super().__init__(_('GlobalConfig setting %(key)s was not found.') % {'key': key})
        self.key = key


class GlobalConfigValueError(GlobalConfigError):
    """
    Report an empty required value or a value that does not satisfy its declared type.

    Expose the key and the type, when available, without including the stored value in the message.
    """

    def __init__(self, key: str, value_type: Any | None = None) -> None:
        if value_type is None:
            message = _('GlobalConfig setting %(key)s has an invalid value.') % {'key': key}
        else:
            message = _('GlobalConfig setting %(key)s has an invalid value for type %(value_type)s.') % {
                'key': key,
                'value_type': value_type,
            }
        super().__init__(message)
        self.key = key
        self.value_type = value_type


class GlobalConfigParseError(GlobalConfigValueError):
    """
    Report a stored value that cannot be converted to its declared runtime type.
    """


class GlobalConfigSnapshotIncompleteError(GlobalConfigError):
    """
    Report the declared keys missing from the database when a full snapshot is built.

    Expose the missing keys as a set and sort them in the message for deterministic output.
    """

    def __init__(self, missing_keys: set[str]) -> None:
        sorted_keys = sorted(missing_keys)
        super().__init__(
            _('Cannot build the GlobalConfig snapshot. Missing settings: %(keys)s.') % {'keys': ', '.join(sorted_keys)}
        )
        self.missing_keys = missing_keys


class GlobalConfigRefreshLockTimeoutError(GlobalConfigError):
    """
    Report an expired wait for the cache refresh lock when the operation cannot proceed.
    """

    def __init__(self) -> None:
        super().__init__(_('Timed out waiting for the GlobalConfig cache refresh lock.'))


class GlobalConfigCreationForbiddenError(GlobalConfigError):
    """
    Report an attempt to create a settings row outside definition initialization.
    """


class GlobalConfigDeletionForbiddenError(GlobalConfigError):
    """
    Report an attempt to delete a settings row through the model or a Django queryset.
    """


class GlobalConfigLockNotOwnedError(GlobalConfigError):
    """
    Report an attempt to publish cache entries or release a refresh lock after losing ownership.
    """
