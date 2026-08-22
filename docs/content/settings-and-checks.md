---
title: Settings and checks
sidebar_position: 9
---

<Since v="1.0.1" />
<Changed v="1.0.1" />

| Setting | Default | Meaning |
|---|---|---|
| `GLOBAL_CONFIG_CATEGORIES` | `()` | sequence of `CategoryDefinition` |
| `GLOBAL_CONFIG_DEFINITIONS` | `()` | sequence of `SettingDefinition` |
| `GLOBAL_CONFIG_ENCRYPTION_KEY` | unset | secret string for `SECURE` values |
| `GLOBAL_CONFIG_CACHE_ALIAS` | `'default'` | Django cache alias |

These three project settings belong in Django `settings`: categories, keys,
and the encryption key. Without `GLOBAL_CONFIG_ENCRYPTION_KEY`, `SECURE`
values are stored as plain text.

## Optional Celery

```bash
pip install 'django-gc[celery]'
```

The task name is `django_gc.refresh_global_configs_cache`. Queue and beat schedule belong to the project.

```python
from django_gc.tasks import refresh_global_configs_cache
```

## Recommendations

Keep keys in a project `StrEnum` and pass that member to `get_value()` and
`set_value()`. Do not scatter raw key strings at call sites.

Use a shared cache backend in multi-process deployments. Locmem does not share a snapshot across workers.
