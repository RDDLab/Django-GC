---
title: Обновление и эксплуатация
---

<Changed v="1.1.5" />

## Обновление с 1.1.4

1. Примените миграции схемы.
2. Объявите текущие настройки проекта и зарегистрируйте провайдеры библиотек. При переименовании ключа укажите его прежнее имя в `SettingDefinition.previous_keys`.
3. Выполните `initialize_global_configs` до запуска веб-процессов и воркеров. Повторяйте команду при изменении объявлений.
4. Запустите проверки Django и убедитесь, что приложение читает ожидаемую настройку.

```bash
python manage.py migrate
python manage.py initialize_global_configs
python manage.py check
```

Инициализация создаёт недостающие категории и ключи. Сохранённое значение канонического ключа имеет приоритет. Если у нескольких прежних ключей для одного отсутствующего канонического ключа разные значения, команда сообщит о конфликте. Устраните расхождение и повторите запуск. Прежние строки сохраняются для отката и исключаются из рабочего кэша.

Если проверки подключённого приложения требуют готовых ключей, примените схему через `python manage.py migrate --skip-checks`, затем выполните инициализацию и обычный `check`.

## Общий снимок кэша

Для веб-процессов и воркеров используйте общий кэш, например Redis или Valkey. Алиас задайте через `GLOBAL_CONFIG_CACHE_ALIAS`, а окружения разделите настройкой Django `KEY_PREFIX`. Перед использованием типа `SECURE` задайте `GLOBAL_CONFIG_ENCRYPTION_KEY` через хранилище секретов окружения.

```python
from django_gc import is_cache_ready, refresh_cache

if not is_cache_ready():
    refresh_cache()
```

`is_cache_ready()` проверяет маркер и записи для всех объявленных ключей. `refresh_cache()` пересобирает снимок из базы под общей блокировкой. Если нужных строк нет, выполните инициализацию с объявлениями текущего выпуска и проверьте алиас кэша. Алгоритм обновления описан в разделе [Кэш](./cache.md), а фоновая задача Celery — в разделе [Настройки](./settings-and-checks.md).

## Изменение связанных настроек в одной транзакции

Пользуйтесь типизированным API для записи. Если несколько процессов могут одновременно менять связанные параметры, заблокируйте строки в транзакции и прочитайте актуальные значения из базы перед расчётом изменений.

```python
from django.db import transaction
from django_gc import set_typed_value
from django_gc.services import GlobalConfigService


with transaction.atomic():
    keys = ["platform.requests_per_minute", "platform.burst_limit"]
    service = GlobalConfigService()
    service.lock_values(keys=keys)
    current = service.get_values(keys=keys, use_cache=False)
    limit = max(current["platform.requests_per_minute"], 60)
    set_typed_value(key="platform.requests_per_minute", value=limit)
    set_typed_value(key="platform.burst_limit", value=max(current["platform.burst_limit"], limit))
```

Объявите оба ключа до запуска примера. Запись обновляет кэш после фиксации транзакции. Защищённые ключи изменяются через сценарий и проверку полномочий провайдера. См. [Объявления](./definitions.md) и [Справочник API](./api-reference.md).
