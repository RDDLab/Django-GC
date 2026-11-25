![Logo](https://github.com/RDDLab/Django-GlobalConfig/raw/main/docs/static/img/logo.svg)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Version: 1.1.5](https://img.shields.io/badge/version-1.1.5-blue.svg?style=for-the-badge)](https://github.com/RDDLab/Django-GlobalConfig/releases/tag/1.1.5)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json&style=for-the-badge)](https://docs.astral.sh/ruff)
[![pyrefly](https://img.shields.io/endpoint?url=https://pyrefly.org/badge.json&style=for-the-badge)](https://pyrefly.org)
[![PyPI](https://img.shields.io/pypi/v/django-gc?style=for-the-badge)](https://pypi.org/project/django-gc/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/django-gc.svg?style=for-the-badge)](https://pypi.python.org/pypi/django-gc/)
[![PyPI djversions](https://img.shields.io/pypi/djversions/django-gc.svg?style=for-the-badge)](https://pypi.org/project/django-gc/)
[![PyPI status](https://img.shields.io/pypi/status/django-gc.svg?style=for-the-badge)](https://pypi.python.org/pypi/django-gc)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/django-gc?style=for-the-badge)](https://pypistats.org/packages/django-gc)
[![PyPI - Types](https://img.shields.io/pypi/types/django-gc.svg?style=for-the-badge)](https://pypi.python.org/pypi/django-gc)

---

[![Tests](https://img.shields.io/github/actions/workflow/status/RDDLab/Django-GlobalConfig/testing.yml?branch=main&label=Tests)](https://github.com/RDDLab/Django-GlobalConfig/actions/workflows/testing.yml)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/RDDLab/Django-GlobalConfig/main.svg)](https://results.pre-commit.ci/latest/github/RDDLab/Django-GlobalConfig/main)

---

**Documentation**: <a href="https://django-gc.rdd-lab.com/" target="_blank">https://django-gc.rdd-lab.com/</a>

**Source Code**: <a href="https://github.com/RDDLab/Django-GlobalConfig" target="_blank">https://github.com/RDDLab/Django-GlobalConfig</a>

---

# Django-GC

Django-GC stores typed runtime settings in the database and serves them from Django's cache. Application code never reads a value through the ORM. The project owns the keys; this package is the mechanism.

## Features

- **Code-declared keys** — categories and definitions live in Django settings and are synchronized by `initialize_global_configs`.
- **Typed values** — strings, numbers, dates, arrays, choices, JSON, UUID, and optional secure secrets.
- **Targeted cache updates** — saving one setting refreshes only its typed cache entry.
- **Full recovery snapshot** — `get_value()` never falls back to a single-row ORM read on cache miss.
- **Stock Django Admin** — edit values with standard `ModelAdmin` and Django's built-in change history.
- **Optional Celery** — periodic full snapshot refresh.
- **Fully typed** — ships `py.typed`; compatible with pyrefly and standard type checkers.

## Requirements

| Python | Minimum Django |
|---|---|
| 3.12, 3.13, 3.14 | 6.0 |
| 3.15 | 6.1.3 |

## Installation

```bash
pip install 'django-gc>=1.1.5'
```

```python
INSTALLED_APPS = [
    'django_gc',
    'django.contrib.admin',
    # ...
]
```

Periodic refresh is optional:

```bash
pip install 'django-gc[celery]'
```

## Quick start

Declare categories and keys in Django settings. Set the encryption key through your deployment configuration before using `SECURE` values.

```python
from enum import StrEnum

from django_gc import (
    CategoryDefinition,
    SettingDefinition,
    SettingType,
)


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
```

```bash
python manage.py migrate
python manage.py initialize_global_configs
```

After Django has initialized, use the runtime API from application code.

```python
from django_gc import get_value, set_typed_value

enabled = get_value("platform.maintenance_enabled")
set_typed_value(key="platform.maintenance_enabled", value=True)
```

## Documentation

[Getting started](https://django-gc.rdd-lab.com/docs/getting-started/) · [Upgrade and operations](https://django-gc.rdd-lab.com/docs/operations/) · [Documentation deployment](.github/docs/README.md)

После создания схемы и при обновлении definitions выполните `uv run python manage.py initialize_global_configs`. Миграции не создают категории и значения GC. Существующие значения сохраняются.

The metadata template uses the standard Django template loader. Project templates may override its logical name.
