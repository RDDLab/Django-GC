---
title: How it works
sidebar_position: 3
---

<Since v="1.0.1" />
<Changed v="1.0.3" />

Runtime code reads values only through `get_value()`. ORM reads of a single key, custom cache-aside keys, and domain fallbacks are out of scope for this package.

```mermaid
flowchart TD
    A["get_value(key)"] --> B{"typed DTO in cache?"}
    B -->|yes| C["resolve value"]
    B -->|miss / legacy| D["LOCK global-config:refresh-lock"]
    D --> E{"another process published?"}
    E -->|yes| C
    E -->|no| F["SELECT all GlobalConfig"]
    F --> G{"all declared keys present?"}
    G -->|no| H["GlobalConfigSnapshotIncompleteError"]
    G -->|yes| I["parse + set_many if lock owned"]
    I --> J["snapshot-ready = true"]
    J --> C
    C --> K{"SECURE?"}
    K -->|yes| L["decrypt in memory"]
    K -->|no| M["typed value / None"]
```

## Read contract

1. Read `global-config:{key}` from Django cache.
2. Accept only a `GlobalConfigCacheValueDTO`. Legacy untyped entries are a miss.
3. On miss, wait for `global-config:refresh-lock`.
4. After acquiring the lock, re-check the requested key.
5. If another process has not published, read every `GlobalConfig` row.
6. Fail if any declared definition key is missing.
7. Parse the full snapshot. One parse failure aborts publish.
8. Publish values and the readiness marker with `set_many` while the lock is still owned.
9. Resolve the requested key. `SECURE` is decrypted only in memory.

There is no single-row database fallback in `get_value()`. Keys have no TTL. A committed save refreshes that key directly; full refresh handles cache-miss recovery and reconciliation.

## Refresh triggers

- synchronous cache miss
- targeted refresh of the saved key after `post_save` via `transaction.on_commit()`
- `post_migrate` after initialization
- optional Celery task `django_gc.refresh_global_configs_cache`

Initialization suppresses per-row refresh and schedules one full commit-time refresh.

Rows live in explicit tables `global_configs` and `global_config_categories`.
