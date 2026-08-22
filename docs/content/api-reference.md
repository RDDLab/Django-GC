---
title: API Reference
sidebar_position: 10
---

<Since v="1.0.1" />
<Changed v="1.0.1" />

```python
from django_gc import (
    CategoryDefinition,
    SettingDefinition,
    SettingType,
    get_value,
    set_value,
    refresh_cache,
    is_cache_ready,
)
```

## Functions

| Function | Returns | Notes |
|---|---|---|
| `get_value(key)` | typed value | `str` or `StrEnum`; may refresh the snapshot |
| `set_value(key, value)` | `GlobalConfig` | existing keys only |
| `refresh_cache()` | `int` | published key count, or `0` if another owner already published |
| `is_cache_ready()` | `bool` | marker + every declared DTO, no database |

## Definitions

`CategoryDefinition(id, code, name)`

`SettingDefinition(key, description, default_value, value_type, category_id, nullable=False, is_read_only=False, variables=None, is_always_update=False)`

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
definitions on `post_migrate`, not from Admin, `save()`, or `set_value()`.

### `GlobalConfigDeletionForbiddenError`

Any `delete()` of a `GlobalConfig` row (`pre_delete` signal). Keys are not
removed when a definition disappears.

### `GlobalConfigLockNotOwnedError`

The process lost `global-config:refresh-lock` before publishing or releasing
it (lock TTL expired). Publish then fails and the snapshot is not written.
A failed `release()` after a successful publish is logged and not re-raised.

Internal classes (`GlobalConfigService`, cache DTO, lock) are not part of the stable import surface. Prefer the module-level functions.
