---
title: Getting Started
sidebar_position: 2
---

<Since v="1.0.1" />

This page is the shortest path from an empty Django project to a working Django-GC snapshot.

## Installation

```bash
pip install django-gc
```

```python
INSTALLED_APPS = [
    'django_gc',
    'django.contrib.admin',
    # ...
]
```

Use a shared cache in production (Redis, Valkey, or another remote backend). The test suite uses locmem.

## Django settings

Categories, keys, and the encryption key live in the Django project's
`settings` — usually the project or app `settings.py`. After
`INSTALLED_APPS`, fill three settings:

1. `GLOBAL_CONFIG_CATEGORIES` — category catalog
2. `GLOBAL_CONFIG_DEFINITIONS` — typed keys
3. `GLOBAL_CONFIG_ENCRYPTION_KEY` — secret used for `SECURE` values

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
    ),
]
GLOBAL_CONFIG_ENCRYPTION_KEY = 'replace-with-a-long-random-secret'
```

Without `GLOBAL_CONFIG_ENCRYPTION_KEY`, `SECURE` values are stored as plain text.

Then migrate:

```bash
python manage.py migrate
```

`post_migrate` creates missing categories and keys. Existing live values are never overwritten.

## Read and write

```python
from django_gc import get_value, set_value

enabled = get_value(SettingKey.MAINTENANCE_ENABLED)
set_value(SettingKey.MAINTENANCE_ENABLED, True)
```

Keep keys in a project `StrEnum` and pass that member to `get_value()` and
`set_value()`. Raw strings work, but the enum is the recommended call site.
