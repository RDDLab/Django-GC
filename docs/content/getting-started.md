---
title: Getting Started
sidebar_position: 2
---

<Since v="1.0.1" />

This page is the shortest path from an empty Django project to a working Django-GC snapshot.

## Installation

```bash
pip install 'django-gc>=1.1.6'
```

```python
INSTALLED_APPS = [
    'django_gc',
    'django.contrib.admin',
    # ...
]
```

<Changed v="1.1.6" />

Configure a shared cache such as Redis or Valkey to serve settings from a snapshot. With Django’s default `LocMemCache` or `DummyCache`, settings are read directly from the database.

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
    ),
]
GLOBAL_CONFIG_ENCRYPTION_KEY = 'replace-with-a-long-random-secret'
```

Without `GLOBAL_CONFIG_ENCRYPTION_KEY`, `SECURE` values are stored as plain text.

Then migrate:

```bash
python manage.py migrate
python manage.py initialize_global_configs
```

<Changed v="1.1.5" />

Migrations create the schema only. Run `python manage.py initialize_global_configs` explicitly to create categories and keys; existing live values are preserved.

## Read and write

```python
from django_gc import get_value, set_typed_value

enabled = get_value(SettingKey.MAINTENANCE_ENABLED)
set_typed_value(key=SettingKey.MAINTENANCE_ENABLED, value=True)
```

Keep keys in a project `StrEnum` and pass that member to `get_value()` and
`set_typed_value()`. Raw strings work, but the enum is the recommended call site.
