---
title: Django-GC
sidebar_label: Главная
slug: /
sidebar_position: 1
---

<Since v="1.0.1" />

## Что такое Django-GC

Django-GC хранит типизированные runtime-настройки в базе и отдаёт их из Django cache. Прикладной код не читает значение через ORM. Проект владеет ключами; этот пакет — механизм.

Это не замена `django.conf.settings`. Статические настройки деплоя остаются в Django settings. Пакет нужен для значений, которые оператор меняет в runtime: флаги, лимиты, ротируемые секреты и похожие ручки.

## Обзор

- [Начало работы](./getting-started.md) — установка, `INSTALLED_APPS`, первые definitions.
- [Как это работает](./how-it-works.md) — снимок, lock, разбор и путь чтения.
- [Definitions](./definitions.md) — `CategoryDefinition`, `SettingDefinition` и `post_migrate`.
- [Типы](./types.md) — каждый `SettingType` и формат хранения.
- [Admin](./admin.md) — стандартный `ModelAdmin`, read-only ключи и формы.
- [История](./history.md) — история Django Admin через `LogEntry`.
- [Кэш](./cache.md) — ключи Django cache, readiness и lock.
- [Настройки и проверки](./settings-and-checks.md) — settings, ключ шифрования, необязательный Celery.
- [Справочник API](./api-reference.md) — публичные функции, классы и исключения.

## Требования

- Python 3.12+
- Django 6.0+

Celery необязателен и нужен только для периодического refresh:

```bash
pip install 'django-gc[celery]'
```
