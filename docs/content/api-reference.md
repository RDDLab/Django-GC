---
title: API Reference
sidebar_position: 10
---

<Since v="1.0.1" />
<Changed v="1.0.3" />

```python
from django_gc import (
    CategoryDefinition,
    SettingDefinition,
    SettingType,
    get_value,
    set_value,
    set_typed_value,
    refresh_cache,
    is_cache_ready,
)
```

You can import the public functions before Django initializes. Call them after Django has loaded its apps.

## Functions

| Function | Returns | Notes |
|---|---|---|
| `get_value(key, *, use_cache=True)` | typed value | accepts a `str` or `StrEnum` key. Reads the database with a local or dummy backend or with `use_cache=False` |
| `set_value(key, value)` | `GlobalConfig` | existing keys only; refreshes that cache entry after commit |
| `set_typed_value(*, key, value)` | `GlobalConfig` | added in 1.1.5. Validates and serializes a typed value for the declared key |
| `refresh_cache()` | `int` | published key count, or `0` when another owner already published or a shared cache is unavailable by configuration |
| `is_cache_ready()` | `bool` | checks the marker and every declared DTO. Returns `False` in database mode |

## Reading and locking multiple settings

<Since v="1.1.5" />

`GlobalConfigService().get_values(keys=keys, use_cache=False)` reads the keys from the database in one query and returns typed values by key. It raises `GlobalConfigNotFoundError` if a key is missing. Use `GlobalConfigService().lock_values(keys=keys)` inside a transaction before computing related writes. See the [transaction example](./operations.md#change-related-values-in-one-transaction).

## Definitions

`CategoryDefinition(id, code, name)`

`SettingDefinition(key, description, default_value, value_type, category_id, nullable=False, is_read_only=False, variables=None, is_always_update=False, previous_keys=[])`

## Exceptions

All exceptions inherit `GlobalConfigError`. Catch that type when the caller
only needs to know that Django-GC failed.

```python
from django_gc import (
    GlobalConfigError,
    GlobalConfigNotFoundError,
    GlobalConfigValueError,
    GlobalConfigParseError,
    GlobalConfigSnapshotIncompleteError,
    GlobalConfigRefreshLockTimeoutError,
    GlobalConfigCreationForbiddenError,
    GlobalConfigDeletionForbiddenError,
    GlobalConfigLockNotOwnedError,
)
```

### `GlobalConfigError`

Base class. The package never raises it directly.

### `GlobalConfigNotFoundError`

The key is not in the snapshot.

- `get_value(key)` — after a full refresh the cache still has no typed DTO
  for that key (the key is missing from definitions or was never initialized).
- `set_value(key, value)` — no `GlobalConfig` row exists for that key.

Attribute: `key`.

### `GlobalConfigValueError`

The stored value cannot be used as the declared type.

- Snapshot refresh — a non-nullable key has `NULL` or `''`.
- Snapshot refresh — `value_type` is not a supported `SettingType`.

Attributes: `key`, `value_type`.

### `GlobalConfigParseError`

Subclass of `GlobalConfigValueError`. The raw text failed conversion.

- Snapshot refresh — `int` / `json.loads` / date parse / similar raises
  `TypeError`, `ValueError`, `SyntaxError`, or `JSONDecodeError`. One
  failure aborts the whole publish.
- `get_value(key)` — a `SECURE` value could not be decrypted
  (`GLOBAL_CONFIG_ENCRYPTION_KEY` missing, wrong, or ciphertext invalid).

### `GlobalConfigSnapshotIncompleteError`

Raised during a locked refresh when the database is missing at least one
key declared in `GLOBAL_CONFIG_DEFINITIONS`. The snapshot is not published.

Attribute: `missing_keys` (`set[str]`).

### `GlobalConfigRefreshLockTimeoutError`

`refresh_cache()` (including a miss inside `get_value()`) waited 35 seconds
for `global-config:refresh-lock` and the snapshot is still not ready. If
another process published in time, this is not raised.

### `GlobalConfigCreationForbiddenError`

`GlobalConfig.save()` on a new row. Keys are created only from project
definitions by `initialize_global_configs`, not from Admin, `save()`, or `set_value()`.

### `GlobalConfigDeletionForbiddenError`

Any `delete()` of a `GlobalConfig` row (`pre_delete` signal). Keys are not
removed when a definition disappears.

### `GlobalConfigLockNotOwnedError`

The process lost `global-config:refresh-lock` before publishing or releasing
it (lock TTL expired). Publish then fails and the snapshot is not written.
A failed `release()` after a successful publish is logged and not re-raised.

Internal classes (`GlobalConfigService`, cache DTO, lock) are not part of the stable import surface. Prefer the module-level functions.


## initialize_global_configs

<Since v="1.1.5" />

```shell
python manage.py initialize_global_configs
```

Explicitly synchronize project and provider definitions after the GC schema exists. Creates missing categories/keys and preserves stored values; only code-owned metadata is updated. Repeating the command is safe. It skips dependent system checks only for this initialization operation. Normal `check` and server startup still validate configuration. No `post_migrate` receiver creates GC data. If tables are absent, the command fails with a schema-migration instruction.
