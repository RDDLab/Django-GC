import base64
import hashlib
from collections.abc import Sequence
from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings

from django_gc.dto import CategoryDefinition, SettingDefinition

_REFRESH_SUPPRESSED: ContextVar[bool] = ContextVar('global_config_refresh_suppressed', default=False)


def get_cache_alias() -> str:
    """
    Return the configured Django cache alias, defaulting to the default cache.
    """
    return str(getattr(settings, 'GLOBAL_CONFIG_CACHE_ALIAS', 'default'))


def get_category_definitions() -> Sequence[CategoryDefinition]:
    """
    Collect the categories declared by the project and its configured providers.

    Resolve provider category IDs from the project's registration without consulting the database.
    """
    from django_gc.registry import collect_definitions

    categories, _definitions = collect_definitions(
        categories=getattr(settings, 'GLOBAL_CONFIG_CATEGORIES', []),
        definitions=getattr(settings, 'GLOBAL_CONFIG_DEFINITIONS', [])
    )
    return categories


def get_category_definition(*, category_id: int) -> CategoryDefinition | None:
    """
    Return the active definition for a numeric category ID, or None when it is undeclared.
    """
    for definition in get_category_definitions():
        if definition.id == category_id:
            return definition
    return None


def get_category_name(*, category_id: int) -> str:
    """
    Return the display name for a declared category, or the numeric ID as text when it is undeclared.
    """
    definition = get_category_definition(category_id=category_id)
    return definition.name if definition is not None else str(category_id)


def get_setting_definitions() -> Sequence[SettingDefinition]:
    """
    Collect the active settings declared by the project and its configured providers.

    Validate ownership, category references and alias uniqueness before returning the definitions.
    """
    from django_gc.registry import collect_definitions

    _categories, definitions = collect_definitions(
        categories=getattr(settings, 'GLOBAL_CONFIG_CATEGORIES', []),
        definitions=getattr(settings, 'GLOBAL_CONFIG_DEFINITIONS', [])
    )
    return definitions


def get_required_setting_keys() -> set[str]:
    """
    Return the canonical keys that must be present for the current cache snapshot to be complete.
    """
    return {str(item.key) for item in get_setting_definitions()}


def get_encryption_key() -> str | None:
    """
    Read GLOBAL_CONFIG_ENCRYPTION_KEY, returning None when it is absent or empty.
    """
    key = getattr(settings, 'GLOBAL_CONFIG_ENCRYPTION_KEY', None)
    if key is None or key == '':
        return None
    return str(key)


def _build_fernet(*, key: str) -> Fernet:
    """
    Derive a Fernet key from the UTF-8 encoding of the configured secret using SHA-256 and URL-safe Base64.
    """
    digest = hashlib.sha256(key.encode('utf-8')).digest()
    return Fernet(key=base64.urlsafe_b64encode(digest))


def encrypt_value(*, text: str) -> str:
    """
    Encrypt a secure value with the configured key and return the token as text.

    Return the input text unchanged when no encryption key has been configured.
    """
    key = get_encryption_key()
    if key is None:
        return text
    return _build_fernet(key=key).encrypt(data=text.encode('utf-8')).decode('ascii')


def decrypt_value(*, text: str) -> str | None:
    """
    Decrypt a stored secure value with the configured key.

    Return the input unchanged when encryption is disabled, or None when a token cannot be decoded or
    authenticated.
    """
    key = get_encryption_key()
    if key is None:
        return text
    try:
        return _build_fernet(key=key).decrypt(token=text.encode('ascii')).decode('utf-8')
    except (InvalidToken, ValueError):
        return None


def is_refresh_suppressed() -> bool:
    """
    Report whether the current execution context has disabled post-save cache refresh callbacks.
    """
    return _REFRESH_SUPPRESSED.get()


@contextmanager
def suppress_cache_refresh() -> Any:
    """
    Suppress per-row refresh callbacks while synchronizing definitions.

    Restore the previous setting on exit, including when the operation raises or scopes are nested.
    """
    token: Token[bool] = _REFRESH_SUPPRESSED.set(True)
    try:
        yield
    finally:
        _REFRESH_SUPPRESSED.reset(token)
