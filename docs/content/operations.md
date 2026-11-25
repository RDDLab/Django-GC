---
title: Upgrade and operations
---

<Changed v="1.1.5" />

## Upgrade from 1.1.4

1. Apply the schema migrations.
2. Declare the current project definitions and register the library providers. For a renamed key, place its old name in `SettingDefinition.previous_keys`.
3. Run `initialize_global_configs` before starting web processes and workers. Repeat it whenever you change the definitions.
4. Run Django system checks and confirm that the application can read an expected setting.

```bash
python manage.py migrate
python manage.py initialize_global_configs
python manage.py check
```

Initialization creates missing categories and keys. If the canonical key already has a stored value, that value takes precedence. If several old keys contain different values for one missing canonical key, initialization reports a conflict. Resolve the old values before retrying. Retired rows remain available for rollback and are excluded from the active cache.

If an integrating app has system checks that require initialized keys, use `python manage.py migrate --skip-checks` for the schema step, then run initialization and the regular `check` command.

## Share and verify the snapshot

Use a shared cache such as Redis or Valkey for web processes and workers. Select the alias with `GLOBAL_CONFIG_CACHE_ALIAS` and isolate deployments with Django's `KEY_PREFIX`. Define `GLOBAL_CONFIG_ENCRYPTION_KEY` through the deployment secret store before using `SECURE` settings.

```python
from django_gc import is_cache_ready, refresh_cache

if not is_cache_ready():
    refresh_cache()
```

`is_cache_ready()` checks the marker and the entries for every declared key. `refresh_cache()` rebuilds the snapshot from the database under a shared lock. If required rows are missing, run initialization against the deployed definitions and check the configured cache alias. See [Cache](./cache.md) for the refresh contract and [Settings](./settings-and-checks.md) for the optional Celery task.

## Change related values in one transaction

Use the typed write API for operator or service updates. When concurrent callers must update several keys together, acquire their row locks inside the transaction and read the current database values before computing changes.

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

Declare both keys before using the example. A write refreshes the cache entry after commit. Protected provider keys use the provider's authorization and editing flow. See [Definitions](./definitions.md) and the [API reference](./api-reference.md).
