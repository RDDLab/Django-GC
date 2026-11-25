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
        nullable=False,
        is_read_only=False,
        variables=None,
        is_always_update=False,
    ),
]
```

## Синхронизация

<Changed v="1.1.5" />

Явная команда `python manage.py initialize_global_configs` вызывает `GlobalConfigInitializationService.initialize()`:

- создать отсутствующие строки категорий с числовыми ID
- создать отсутствующие ключи с объявленным default
- обновить метаданные существующих ключей: description, тип, категория, nullable, read-only, `is_always_update`
- обновить `variables` только при `is_always_update` для choice-типов
- не заменять рабочее `value`
- отклонить ключ, числовая категория которого отсутствует в `GLOBAL_CONFIG_CATEGORIES`
- запланировать один refresh кэша после commit

Новые ключи нельзя создать через `save()` или Admin. Они появляются только из definitions.

## Настройки подключаемых библиотек

<Since v="1.1.5" />

Библиотека владеет схемой и проверками в ConfigurationProvider, проект подключает её через GLOBAL_CONFIG_PROVIDERS вместе со своими определениями, GC хранит единственные рабочие значения и показывает общий каталог. Обратной зависимости GC от предметных библиотек нет.

```python
from django_gc import ProviderDefinition

GLOBAL_CONFIG_PROVIDERS = [
    ProviderDefinition(
        provider='your_library.configuration.RuntimeConfigurationProvider',
        category_ids={'general': 10},
    ),
]
```

Класс наследует django_gc.providers.ConfigurationProvider, объявляет namespace, словарь categories и get_definitions(category_ids=...). Ключ начинается с namespace.; числовые ID категорий назначает проект. Дубликаты namespace, ключей, ID/кодов категорий и неполное соответствие категорий отклоняются явно. GLOBAL_CONFIG_CATEGORIES и GLOBAL_CONFIG_DEFINITIONS сохраняются.

validate(key=..., value=...) проверяет типизированное значение. initial_value(key=..., default=...) переносит прежнее значение только при первом создании ключа GC; повторная инициализация рабочие значения сохраняет. protected=True запрещает обычную запись модели/API без подтверждённой операции владельца. change_view(admin_site=..., request=..., key=...) показывает редактор владельца внутри URL GC после обычной проверки прав GC. Редактор дополнительно проверяет собственные права и подтверждение.

get_value(key, use_cache=False) читает авторитетное значение из базы. set_typed_value(key=..., value=...) проверяет и сериализует типизированное значение. GlobalConfigService.lock_values(keys=...) блокирует существующие ключи в стабильном порядке внутри транзакции владельца до проверки ревизии preview. После проверки подтверждённой операции доверенный код владельца использует django_gc.registry.authorize_changes(keys=[...]) на время записи. Контекст не заменяет авторизацию пользователя. QuerySet.update(), bulk SQL и доступ к базе остаются границами доверенного административного кода и не предоставляются как пользовательский API настроек.

JSON-форма сохраняет списки и скалярные значения. GlobalConfigForm.typed_value() возвращает проверенное типизированное значение без сохранения. Для protected=True владелец разрешает запись после своего подтверждения; прямое сохранение может использовать обычную форму. Учётные данные, политики с отношениями/жизненным циклом и протокольное состояние остаются сущностями. Состав приложений, backend, зависимости запуска и секреты шифрования/bootstrap остаются Django settings.

## Единый формат и перенос ключей

<Changed v="1.1.5" />

Новые ключи соответствуют `^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$`. Пример: `project.name`. При переименовании задайте `previous_keys=['project-name']` в новом `SettingDefinition` и выполните `uv run python manage.py initialize_global_configs` до запуска приложения. Каноническое значение никогда не перезаписывается. Если его ещё нет, команда копирует сохранённое значение прежнего ключа, включая зашифрованную строку SECURE без повторного шифрования; только при отсутствии прежнего ключа используется `initial_value/default_value`.

Неоднозначные прежние значения, несовпадающий тип или пересечение имён явно отклоняются. Прежние строки сохраняются для отката, скрыты из каталога и исключены из рабочего снимка кэша. Чтение, запись и блокировка через публичный API разрешают старое имя в каноническое до доступа к кэшу и проверок владельца. Прямой SQL остаётся доверенной административной границей.


## Права владельца и атомарное сохранение

<Changed v="1.1.5" />

`has_view_permission(request=...)` и `has_change_permission(request=...)` добавляют ограничения владельца к обычным правам модели GC. По умолчанию действует стандартная проверка GC; методы сами по себе доступ не выдают. `GlobalConfig.save()` атомарен: обработчики pre_save/post_save владельца могут сохранить активацию и диагностику вместе с желаемым значением. Кэш обновляется после commit. GC не импортирует предметные библиотеки и не навязывает им сценарий подтверждения политик.
