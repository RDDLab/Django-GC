---
title: Definitions
sidebar_position: 4
---

<Since v="1.0.1" />
<Changed v="1.1.4" />

The library does not ship product keys. The Django app declares categories
and keys in project `settings`, together with `GLOBAL_CONFIG_ENCRYPTION_KEY`.

Categories are code-owned presentation metadata. `GlobalConfigCategory`
persists only the numeric `SettingDefinition.category_id`, and
`GlobalConfig` keeps its foreign key to that row. Admin resolves category
codes and display names from `GLOBAL_CONFIG_CATEGORIES`. Declare the catalog
with `CategoryDefinition` entries; no category Enum is required.

Keep keys in a project `StrEnum`. Use the same member in `SettingDefinition`,
`get_value()`, and `set_value()`.

```python
from enum import StrEnum

from django_gc import CategoryDefinition, SettingDefinition, SettingType


class SettingKey(StrEnum):
    MAINTENANCE_ENABLED = 'platform.maintenance_enabled'


GLOBAL_CONFIG_CATEGORIES = [
    CategoryDefinition(id=1, code='platform', name='Platform'),
]

GLOBAL_CONFIG_DEFINITIONS = [
    SettingDefinition(
        key=SettingKey.MAINTENANCE_ENABLED,
        description='Maintenance mode',
        default_value=False,
        value_type=SettingType.BOOLEAN,
        category_id=1,
        nullable=False,
        is_read_only=False,
        variables=None,
        is_always_update=False,
    ),
]
```

## Synchronization

<Changed v="1.1.5" />

The explicit command `python manage.py initialize_global_configs` calls `GlobalConfigInitializationService.initialize()`:

- create missing numeric category rows
- create missing keys with the declared default
- update metadata on existing keys: description, type, category, nullable, read-only, `is_always_update`
- update `variables` only when `is_always_update` is true for a choice type
- never replace a live `value`
- reject a key whose numeric category is absent from `GLOBAL_CONFIG_CATEGORIES`
- schedule one cache refresh after commit

New keys cannot be created through `save()` or Admin. They appear only from definitions.

## Library-owned configuration

<Since v="1.1.5" />

Libraries declare their keys and validation in a `ConfigurationProvider`. The project composes providers with its own definitions; GC owns the database values and the common Admin catalog. GC never imports a domain library automatically.

```python
from django_gc import ProviderDefinition

GLOBAL_CONFIG_PROVIDERS = [
    ProviderDefinition(
        provider='your_library.configuration.RuntimeConfigurationProvider',
        category_ids={'general': 10},
    ),
]
```

Subclass `django_gc.providers.ConfigurationProvider`. Declare a unique `namespace`, category codes/names, and `get_definitions(category_ids=...)`. Keys must start with `namespace.`. Category IDs belong to the project and must be unique positive small integers. Duplicate keys, namespaces, IDs/codes and incomplete category mappings fail explicitly. Existing `GLOBAL_CONFIG_CATEGORIES` and `GLOBAL_CONFIG_DEFINITIONS` continue to work.

`validate(key=..., value=...)` checks typed values. `initial_value(key=..., default=...)` imports an old value only when that GC key does not exist; repeat initialization preserves live values. `protected=True` denies ordinary model/API writes outside an owner-authorized change. `change_view(admin_site=..., request=..., key=...)` supplies the owner's editor at the GC URL, after normal GC permissions are checked. The owner must additionally enforce its own permissions and confirmation workflow.

`get_value(key, use_cache=False)` reads the authoritative database value inside a protected transaction. `set_typed_value(key=..., value=...)` serializes typed values and runs owner validation. `GlobalConfigService.lock_values(keys=...)` locks existing keys in stable order inside the owner's transaction before checking a preview revision. After verifying a confirmed operation, trusted owner code uses `django_gc.registry.authorize_changes(keys=[...])` around its write. This context is a trusted-code boundary, not user authorization. `QuerySet.update()`, bulk SQL and database credentials remain trusted administrative boundaries and must not be exposed as configuration endpoints.

JSON forms preserve lists and scalar values. `GlobalConfigForm.typed_value()` returns the validated typed value without saving. A provider using protected=True must authorize its own confirmed operation before writing; providers with direct saves may use ordinary forms. Credentials, policies with relationships/lifecycle, and protocol state stay domain entities. Startup dependencies, installed apps, backends and encryption/bootstrap secrets remain Django settings.

## Canonical names and explicit renames

<Changed v="1.1.5" />

New keys match `^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$`, for example `project.name`. Declare `previous_keys=['project-name']` on the new `SettingDefinition`, then run `uv run python manage.py initialize_global_configs` before starting the application. An existing canonical value always wins. If it is missing, initialization copies the stored previous value, including SECURE ciphertext without double encryption. Only when no previous row exists does `initial_value/default_value` apply.

Ambiguous previous values, different value types and overlapping names fail explicitly. Previous rows remain for rollback, are hidden from the catalog and excluded from the active cache snapshot. Public reads, writes and locks resolve aliases before cache access and owner authorization. Direct SQL remains a trusted administrative boundary.


## Owner permissions and atomic saves

<Changed v="1.1.5" />

`has_view_permission(request=...)` and `has_change_permission(request=...)` add owner restrictions to normal GC model permissions. Defaults allow the standard GC permission decision. They do not grant access on their own. `GlobalConfig.save()` is atomic, so owner pre_save/post_save receivers can persist an activation snapshot and diagnostics with the desired value. Cache callbacks still run after commit. GC does not import domain libraries or require their policy workflow.
