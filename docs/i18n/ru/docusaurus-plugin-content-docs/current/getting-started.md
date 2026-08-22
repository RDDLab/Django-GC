---
title: Начало работы
sidebar_position: 2
---

<Since v="1.0.1" />

Короткий путь от пустого Django-проекта до рабочего снимка Django-GC.

## Установка

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

В production используйте общий кэш (Redis, Valkey или другой remote backend). Тесты используют locmem.

## Django settings

Категории, ключи и ключ шифрования описываются в `settings` Django-проекта —
обычно в `settings.py` проекта или приложения. После `INSTALLED_APPS`
заполните три настройки:

1. `GLOBAL_CONFIG_CATEGORIES` — каталог категорий
2. `GLOBAL_CONFIG_DEFINITIONS` — типизированные ключи
3. `GLOBAL_CONFIG_ENCRYPTION_KEY` — секрет для значений `SECURE`

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

Без `GLOBAL_CONFIG_ENCRYPTION_KEY` значения `SECURE` хранятся открытым текстом.

Затем migrate:

```bash
python manage.py migrate
```

`post_migrate` создаёт отсутствующие категории и ключи. Уже существующие рабочие значения не перезаписываются.

## Чтение и запись

```python
from django_gc import get_value, set_value

enabled = get_value(SettingKey.MAINTENANCE_ENABLED)
set_value(SettingKey.MAINTENANCE_ENABLED, True)
```

Ключи держите в проектном `StrEnum` и передавайте член enum в `get_value()` и
`set_value()`. Строка тоже работает, но вызов через enum — рекомендуемый.
