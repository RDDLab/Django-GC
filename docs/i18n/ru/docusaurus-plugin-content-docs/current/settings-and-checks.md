---
title: Настройки и проверки
sidebar_position: 9
---

<Since v="1.0.1" />
<Changed v="1.0.1" />

| Настройка | По умолчанию | Смысл |
|---|---|---|
| `GLOBAL_CONFIG_CATEGORIES` | `()` | последовательность `CategoryDefinition` |
| `GLOBAL_CONFIG_DEFINITIONS` | `()` | последовательность `SettingDefinition` |
| `GLOBAL_CONFIG_ENCRYPTION_KEY` | не задано | секретная строка для значений `SECURE` |
| `GLOBAL_CONFIG_CACHE_ALIAS` | `'default'` | алиас Django cache |

Эти три настройки проекта живут в Django `settings`: категории, ключи и
ключ шифрования. Без `GLOBAL_CONFIG_ENCRYPTION_KEY` значения `SECURE`
хранятся открытым текстом.

## Необязательный Celery

```bash
pip install 'django-gc[celery]'
```

Имя задачи — `django_gc.refresh_global_configs_cache`. Очередь и beat-расписание задаёт проект.

```python
from django_gc.tasks import refresh_global_configs_cache
```

## Рекомендации

Ключи храните в проектном `StrEnum` и передавайте его в `get_value()` и
`set_value()`. Не размазывайте сырые строки ключей по вызовам.

В multi-process деплое используйте общий cache backend. Locmem не разделяет снимок между воркерами.
