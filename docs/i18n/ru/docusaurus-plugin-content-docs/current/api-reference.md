---
title: Справочник API
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

Импортировать публичные функции можно до инициализации Django. Вызывайте их после загрузки приложений.

## Функции

| Функция | Возвращает | Заметки |
|---|---|---|
| `get_value(key, *, use_cache=True)` | типизированное значение | принимает ключ `str` или `StrEnum`. Читает базу с локальным или dummy-кэшем либо с `use_cache=False` |
| `set_value(key, value)` | `GlobalConfig` | только существующие ключи; после commit обновляет этот cache entry |
| `set_typed_value(*, key, value)` | `GlobalConfig` | добавлена в 1.1.5. Проверяет и сериализует типизированное значение объявленного ключа |
| `refresh_cache()` | `int` | число опубликованных ключей или `0`, если другой процесс уже опубликовал снимок или общий кэш не настроен |
| `is_cache_ready()` | `bool` | проверяет маркер и каждый объявленный DTO. В режиме чтения из базы возвращает `False` |

## Чтение и блокировка нескольких ключей

<Since v="1.1.5" />

`GlobalConfigService().get_values(keys=keys, use_cache=False)` читает ключи из базы одним запросом и возвращает типизированные значения по ключам. Если ключ отсутствует, сервис выбрасывает `GlobalConfigNotFoundError`. Вызывайте `GlobalConfigService().lock_values(keys=keys)` внутри транзакции до расчёта связанных изменений. См. [пример транзакции](./operations.md).

## Definitions

`CategoryDefinition(id, code, name)`

`SettingDefinition(key, description, default_value, value_type, category_id, nullable=False, is_read_only=False, variables=None, is_always_update=False, previous_keys=[])`

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
проектных definitions командой `initialize_global_configs`, не из Admin, `save()` или
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


## initialize_global_configs

<Since v="1.1.5" />

```shell
python manage.py initialize_global_configs
```

Явно синхронизирует определения проекта и провайдеров после создания схемы GC. Создаёт отсутствующие категории/ключи и сохраняет рабочие значения; обновляются только кодовые метаданные. Повторный запуск безопасен. Зависимые system checks не выполняются только внутри этой команды; обычный check и запуск сервера продолжают проверять конфигурацию. Обработчиков post_migrate для создания данных GC нет. При отсутствии таблиц команда сообщает, что сначала нужно применить миграции схемы.
