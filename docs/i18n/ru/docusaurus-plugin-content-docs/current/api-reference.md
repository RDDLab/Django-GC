---
title: Справочник API
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

## Функции

| Функция | Возвращает | Заметки |
|---|---|---|
| `get_value(key)` | типизированное значение | `str` или `StrEnum`; может обновить снимок |
| `set_value(key, value)` | `GlobalConfig` | только существующие ключи |
| `refresh_cache()` | `int` | число опубликованных ключей или `0`, если снимок уже опубликовал другой владелец |
| `is_cache_ready()` | `bool` | маркер + каждый объявленный DTO, без базы |

## Definitions

`CategoryDefinition(id, code, name)`

`SettingDefinition(key, description, default_value, value_type, category_id, nullable=False, is_read_only=False, variables=None, is_always_update=False)`

## Исключения

Все исключения наследуют `GlobalConfigError`. Ловите этот тип, если
вызывающему коду достаточно знать, что Django-GC завершился ошибкой.

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

Базовый класс. Пакет сам его не поднимает.

### `GlobalConfigNotFoundError`

Ключа нет в снимке.

- `get_value(key)` — после полного refresh в кэше всё ещё нет типизированного
  DTO для ключа (ключа нет в definitions или он не был инициализирован).
- `set_value(key, value)` — в таблице нет строки `GlobalConfig` с этим ключом.

Атрибут: `key`.

### `GlobalConfigValueError`

Сохранённое значение нельзя использовать как объявленный тип.

- Refresh снимка — у ключа без `nullable` значение `NULL` или `''`.
- Refresh снимка — `value_type` не входит в поддерживаемые `SettingType`.

Атрибуты: `key`, `value_type`.

### `GlobalConfigParseError`

Подкласс `GlobalConfigValueError`. Сырой текст не удалось преобразовать.

- Refresh снимка — `int` / `json.loads` / разбор даты и т.п. подняли
  `TypeError`, `ValueError`, `SyntaxError` или `JSONDecodeError`. Одна
  ошибка отменяет всю публикацию.
- `get_value(key)` — значение `SECURE` не расшифровалось
  (`GLOBAL_CONFIG_ENCRYPTION_KEY` не задан, неверный или шифротекст битый).

### `GlobalConfigSnapshotIncompleteError`

Во время refresh под lock в базе нет хотя бы одного ключа из
`GLOBAL_CONFIG_DEFINITIONS`. Снимок не публикуется.

Атрибут: `missing_keys` (`set[str]`).

### `GlobalConfigRefreshLockTimeoutError`

`refresh_cache()` (в том числе miss внутри `get_value()`) ждал
`global-config:refresh-lock` 35 секунд, и снимок всё ещё не готов. Если
другой процесс успел опубликовать, исключение не поднимается.

### `GlobalConfigCreationForbiddenError`

`GlobalConfig.save()` для новой строки. Ключи создаются только из
проектных definitions на `post_migrate`, не из Admin, `save()` или
`set_value()`.

### `GlobalConfigDeletionForbiddenError`

Любой `delete()` строки `GlobalConfig` (сигнал `pre_delete`). Ключ не
удаляется, даже если definition исчез.

### `GlobalConfigLockNotOwnedError`

Процесс потерял `global-config:refresh-lock` до публикации или освобождения
(истёк TTL lock). Публикация тогда падает, снимок не записывается.
Неудачный `release()` после успешной публикации только логируется и
повторно не поднимается.

Внутренние классы (`GlobalConfigService`, cache DTO, lock) не входят в стабильный import surface. Предпочитайте функции уровня модуля.
