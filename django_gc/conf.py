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
    Вернуть алиас Django cache для снимка GlobalConfig.
    """
    return str(getattr(settings, 'GLOBAL_CONFIG_CACHE_ALIAS', 'default'))


def get_category_definitions() -> Sequence[CategoryDefinition]:
    """
    Прочитать объявленные проектом категории.
    """
    return tuple(getattr(settings, 'GLOBAL_CONFIG_CATEGORIES', ()))


def get_setting_definitions() -> Sequence[SettingDefinition]:
    """
    Прочитать объявленные проектом ключи.
    """
    return tuple(getattr(settings, 'GLOBAL_CONFIG_DEFINITIONS', ()))


def get_required_setting_keys() -> set[str]:
    """
    Получить системный состав обязательного полного снимка.
    """
    return {str(item.key) for item in get_setting_definitions()}


def get_encryption_key() -> str | None:
    """
    Прочитать ключ шифрования SECURE-значений.
    """
    key = getattr(settings, 'GLOBAL_CONFIG_ENCRYPTION_KEY', None)
    if key is None or key == '':
        return None
    return str(key)


def _build_fernet(*, key: str) -> Fernet:
    """
    Построить Fernet из произвольной секретной строки.
    """
    digest = hashlib.sha256(key.encode('utf-8')).digest()
    return Fernet(key=base64.urlsafe_b64encode(digest))


def encrypt_value(*, text: str) -> str:
    """
    Зашифровать SECURE-значение, если задан GLOBAL_CONFIG_ENCRYPTION_KEY.
    """
    key = get_encryption_key()
    if key is None:
        return text
    return _build_fernet(key=key).encrypt(data=text.encode('utf-8')).decode('ascii')


def decrypt_value(*, text: str) -> str | None:
    """
    Расшифровать SECURE-значение, если задан GLOBAL_CONFIG_ENCRYPTION_KEY.
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
    Проверить, нужно ли пропустить post_save refresh.
    """
    return _REFRESH_SUPPRESSED.get()


@contextmanager
def suppress_cache_refresh() -> Any:
    """
    Подавить per-row refresh на время синхронизации definitions.
    """
    token: Token[bool] = _REFRESH_SUPPRESSED.set(True)
    try:
        yield
    finally:
        _REFRESH_SUPPRESSED.reset(token)
