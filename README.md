![Icon](https://github.com/RDDLab/Django-GC/raw/main/docs/static/img/icon.svg)

![Logo](https://github.com/RDDLab/Django-GC/raw/main/docs/static/img/logo.svg)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json&style=for-the-badge)](https://docs.astral.sh/ruff)
[![pyrefly](https://img.shields.io/endpoint?url=https://pyrefly.org/badge.json&style=for-the-badge)](https://pyrefly.org)
[![PyPI](https://img.shields.io/pypi/v/django-gc?style=for-the-badge)](https://pypi.org/project/django-gc/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/django-gc.svg?style=for-the-badge)](https://pypi.python.org/pypi/django-gc/)
[![PyPI djversions](https://img.shields.io/pypi/djversions/django-gc.svg?style=for-the-badge)](https://pypi.org/project/django-gc/)
[![PyPI status](https://img.shields.io/pypi/status/django-gc.svg?style=for-the-badge)](https://pypi.python.org/pypi/django-gc)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/django-gc?style=for-the-badge)](https://pypistats.org/packages/django-gc)
[![PyPI - Types](https://img.shields.io/pypi/types/django-gc.svg?style=for-the-badge)](https://pypi.python.org/pypi/django-gc)

---

[![Tests](https://img.shields.io/github/actions/workflow/status/RDDLab/Django-GC/testing.yml?branch=main&label=Tests)](https://github.com/RDDLab/Django-GC/actions/workflows/testing.yml)
[![Codecov](https://img.shields.io/codecov/c/github/RDDLab/Django-GC/main?logo=codecov)](https://codecov.io/gh/RDDLab/Django-GC)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/RDDLab/Django-GC/main.svg)](https://results.pre-commit.ci/latest/github/RDDLab/Django-GC/main)

---

**Documentation**: <a href="https://django-gc.rdd-lab.com/" target="_blank">https://django-gc.rdd-lab.com/</a>

**Source Code**: <a href="https://github.com/RDDLab/Django-GC" target="_blank">https://github.com/RDDLab/Django-GC</a>

---

# Django-GC

Django-GC stores typed runtime settings in the database and serves them from Django's cache. Application code never reads a value through the ORM. The project owns the keys; this package is the mechanism.

## Features

- **Code-declared keys** — categories and definitions live in Django settings and are synchronized after migrate.
- **Typed values** — strings, numbers, dates, arrays, choices, JSON, UUID, and optional secure secrets.
- **Full cache snapshot** — `get_value()` never falls back to a single-row ORM read.
- **Stock Django Admin** — edit values with standard `ModelAdmin` and Django's built-in change history.
- **Optional Celery** — periodic full snapshot refresh.
- **Fully typed** — ships `py.typed`; compatible with pyrefly and standard type checkers.

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

Periodic refresh is optional:

```bash
pip install 'django-gc[celery]'
```

## Quick start

In Django `settings`, set categories, keys, and the encryption key. Then migrate and read values through the service:

```python
from enum import StrEnum

from django_gc import (
    CategoryDefinition,
    SettingDefinition,
    SettingType,
    get_value,
    set_value,
)


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

enabled = get_value(SettingKey.MAINTENANCE_ENABLED)
set_value(SettingKey.MAINTENANCE_ENABLED, True)
```

## Documentation

**https://django-gc.rdd-lab.com/**
