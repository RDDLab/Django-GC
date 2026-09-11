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
    MAINTENANCE_ENABLED = 'maintenance-enabled'


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

`GlobalConfigInitializationService.initialize()` runs on `post_migrate` for `django_gc`:

- create missing numeric category rows
- create missing keys with the declared default
- update metadata on existing keys: description, type, category, nullable, read-only, `is_always_update`
- update `variables` only when `is_always_update` is true for a choice type
- never replace a live `value`
- reject a key whose numeric category is absent from `GLOBAL_CONFIG_CATEGORIES`
- schedule one cache refresh after commit

New keys cannot be created through `save()` or Admin. They appear only from definitions.
