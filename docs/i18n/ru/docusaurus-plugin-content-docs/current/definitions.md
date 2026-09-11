---
title: Definitions
sidebar_position: 4
---

<Since v="1.0.1" />
<Changed v="1.1.4" />

Библиотека не поставляет продуктовые ключи. Django-приложение объявляет
категории и ключи в `settings` проекта вместе с
`GLOBAL_CONFIG_ENCRYPTION_KEY`.

Категории — это presentation-метаданные, управляемые кодом.
`GlobalConfigCategory` сохраняет только числовой
`SettingDefinition.category_id`, а `GlobalConfig` сохраняет FK на эту
строку. Admin получает код и отображаемое название из
`GLOBAL_CONFIG_CATEGORIES`. Каталог объявляется обычными
`CategoryDefinition`; отдельный Enum категорий не нужен.

Ключи держите в проектном `StrEnum`. Тот же член передавайте в
`SettingDefinition`, `get_value()` и `set_value()`.

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

## Синхронизация

`GlobalConfigInitializationService.initialize()` выполняется на `post_migrate` приложения `django_gc`:

- создать отсутствующие строки категорий с числовыми ID
- создать отсутствующие ключи с объявленным default
- обновить метаданные существующих ключей: description, тип, категория, nullable, read-only, `is_always_update`
- обновить `variables` только при `is_always_update` для choice-типов
- не заменять рабочее `value`
- отклонить ключ, числовая категория которого отсутствует в `GLOBAL_CONFIG_CATEGORIES`
- запланировать один refresh кэша после commit

Новые ключи нельзя создать через `save()` или Admin. Они появляются только из definitions.
