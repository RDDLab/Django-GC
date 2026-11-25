import re
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.utils.module_loading import import_string
from django.utils.translation import gettext as _

from django_gc.dto import CategoryDefinition, ProviderDefinition, SettingDefinition
from django_gc.providers import ConfigurationProvider

MAX_CATEGORY_ID = 32767
SETTING_KEY_PATTERN = re.compile(r'^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$')

_AUTHORIZED_KEYS: ContextVar[frozenset[str]] = ContextVar('global_config_authorized_keys', default=frozenset())


def get_providers() -> list[tuple[ConfigurationProvider, ProviderDefinition]]:
    """
    Load the provider classes explicitly registered in Django settings.

    Return each provider instance with its registration. Validate unique namespaces and complete category
    mappings without querying the database.
    """
    providers: list[tuple[ConfigurationProvider, ProviderDefinition]] = []
    namespaces: set[str] = set()
    for registration in getattr(settings, 'GLOBAL_CONFIG_PROVIDERS', []):
        if not isinstance(registration, ProviderDefinition):
            raise ImproperlyConfigured('GLOBAL_CONFIG_PROVIDERS must contain ProviderDefinition values.')
        provider_class = import_string(registration.provider)
        if not isinstance(provider_class, type) or not issubclass(provider_class, ConfigurationProvider):
            raise ImproperlyConfigured(f'{registration.provider} must extend ConfigurationProvider.')
        provider = provider_class()
        if not provider.namespace or provider.namespace in namespaces:
            raise ImproperlyConfigured(f'Duplicate or empty GlobalConfig namespace: {provider.namespace!r}.')
        if set(registration.category_ids) != set(provider.categories):
            raise ImproperlyConfigured(f'Category mapping does not match provider {provider.namespace}.')
        namespaces.add(provider.namespace)
        providers.append((provider, registration))
    return providers


def collect_definitions(
    *, categories: Sequence[CategoryDefinition], definitions: Sequence[SettingDefinition]
) -> tuple[list[CategoryDefinition], list[SettingDefinition]]:
    """
    Merge project and provider categories and settings into a single catalog.

    Validate category IDs, ownership, key format and aliases. Raise a configuration error for conflicts or a
    KeyError for an undeclared category reference.
    """
    collected_categories = list(categories)
    collected_definitions = list(definitions)
    for provider, registration in get_providers():
        collected_categories.extend(
            CategoryDefinition(id=registration.category_ids[code], code=f'{provider.namespace}.{code}', name=str(name))
            for code, name in provider.categories.items()
        )
        provider_definitions = provider.get_definitions(category_ids=registration.category_ids)
        for definition in provider_definitions:
            if not str(definition.key).startswith(f'{provider.namespace}.'):
                raise ImproperlyConfigured(f'Key {definition.key!s} is outside namespace {provider.namespace}.')
            if definition.category_id not in registration.category_ids.values():
                raise ImproperlyConfigured(f'Key {definition.key!s} uses another provider category.')
        collected_definitions.extend(provider_definitions)
    ids = [item.id for item in collected_categories]
    codes = [item.code for item in collected_categories]
    keys = [str(item.key) for item in collected_definitions]
    if any(isinstance(category_id, bool) or not isinstance(category_id, int) or not 1 <= category_id <= MAX_CATEGORY_ID
           for category_id in ids):
        raise ImproperlyConfigured('GlobalConfig category IDs must be integers between 1 and 32767.')
    if len(ids) != len(set(ids)) or len(codes) != len(set(codes)) or len(keys) != len(set(keys)):
        raise ImproperlyConfigured('Duplicate GlobalConfig category ID, category code or setting key.')
    previous_keys: set[str] = set()
    for definition in collected_definitions:
        if SETTING_KEY_PATTERN.fullmatch(str(definition.key)) is None:
            raise ImproperlyConfigured(
                f'GlobalConfig key {definition.key!s} must use lowercase <namespace>.<snake_case>.'
            )
        for previous_key in definition.previous_keys:
            if not previous_key or previous_key in keys or previous_key in previous_keys:
                raise ImproperlyConfigured(f'Conflicting GlobalConfig previous key: {previous_key!r}.')
            previous_keys.add(previous_key)
        if definition.category_id not in ids:
            raise KeyError(
                _('GlobalConfig category id=%(category_id)s is not declared.') % {'category_id': definition.category_id}
            )
    return collected_categories, collected_definitions


def resolve_key(*, key: str) -> str:
    """
    Resolve a declared old key to the active canonical key before reads, locks or writes.

    Return unknown names unchanged so normal lookup can report them as missing.
    """
    from django_gc.conf import get_setting_definitions

    for definition in get_setting_definitions():
        if key in definition.previous_keys:
            return str(definition.key)
    return key


def get_provider(*, key: str) -> ConfigurationProvider | None:
    """
    Find the provider that declares the supplied setting.

    Return None for project-owned and unknown keys, even if the latter share a provider's namespace.
    """
    key = resolve_key(key=key)
    for provider, registration in get_providers():
        if key.startswith(f'{provider.namespace}.') and any(
            str(definition.key) == key
            for definition in provider.get_definitions(category_ids=registration.category_ids)
        ):
            return provider
    return None


@contextmanager
def authorize_changes(*, keys: Sequence[str]) -> Iterator[None]:
    """
    Temporarily authorize a list of keys in the current execution context.

    The owning workflow must already have verified the operator and confirmed the action. Resolve aliases
    and restore the previous authorization when the scope exits.
    """
    token = _AUTHORIZED_KEYS.set(_AUTHORIZED_KEYS.get().union(resolve_key(key=key) for key in keys))
    try:
        yield
    finally:
        _AUTHORIZED_KEYS.reset(token)


def validate_change(*, key: str, value: Any) -> Any:
    """
    Validate a typed change through the provider that owns the key.

    Leave unowned values unchanged. Raise PermissionDenied when a protected provider has not authorized the
    key in the current context.
    """
    key = resolve_key(key=key)
    provider = get_provider(key=key)
    if provider is None:
        return value
    if provider.protected and key not in _AUTHORIZED_KEYS.get():
        raise PermissionDenied(_("Confirm the change in the settings provider's editor."))
    return provider.validate(key=key, value=value)
