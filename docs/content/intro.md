---
title: Django-GC
sidebar_label: Home
slug: /
sidebar_position: 1
---

<Since v="1.0.1" />

## What Django-GC is

Django-GC stores typed runtime settings in the database and serves them from Django's cache. Application code never reads a value through the ORM. The project owns the keys; this package is the mechanism.

It is not a replacement for `django.conf.settings`. Static deploy-time settings stay in Django settings. This package is for values operators change at runtime: feature flags, limits, secrets that rotate, and similar knobs.

## Feature overview

- [Getting started](./getting-started.md) — install, `INSTALLED_APPS`, first definitions.
- [How it works](./how-it-works.md) — snapshot, lock, parse, and the read path.
- [Definitions](./definitions.md) — `CategoryDefinition`, `SettingDefinition`, and `initialize_global_configs`.
- [Types](./types.md) — every `SettingType` and its stored format.
- [Admin](./admin.md) — stock `ModelAdmin`, read-only keys, and forms.
- [History](./history.md) — Django Admin `LogEntry` history.
- [Cache](./cache.md) — Django cache keys, readiness, and lock.
- [Settings and checks](./settings-and-checks.md) — settings, encryption key, optional Celery.
- [API reference](./api-reference.md) — public functions, classes, and exceptions.

## Requirements

| Python | Minimum Django |
|---|---|
| 3.12, 3.13, 3.14 | 6.0 |
| 3.15 | 6.1.3 |

CI runs the full test suite with the locked Django version and the minimum for each Python version.
See the [upgrade and operations guide](./operations.md) for the 1.1.5 deployment sequence.

Celery is optional and only needed for a periodic refresh task:

```bash
pip install 'django-gc[celery]'
```
