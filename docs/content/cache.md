---
title: Cache
sidebar_position: 8
---

<Since v="1.0.1" />
<Changed v="1.0.3" />

The snapshot lives in Django's cache, alias `GLOBAL_CONFIG_CACHE_ALIAS` (default `default`).

| Key | Meaning | TTL |
|---|---|---|
| `global-config:{key}` | one typed DTO | none |
| `global-config:snapshot-ready` | full snapshot marker | none |
| `global-config:refresh-lock` | refresh lock | 30 seconds |

Lock wait timeout is 35 seconds. If the wait times out, the service accepts an already published snapshot or raises `GlobalConfigRefreshLockTimeoutError`. It never publishes without owning the lock.

Publish uses `cache.set_many`. On Redis/Valkey this is typically one `MSET`. Locmem is enough for tests and a single process.

After one `GlobalConfig` row is saved and its transaction commits, Django-GC acquires the shared refresh lock, reads that row, and replaces only its typed cache entry. Other entries are not read or changed. Full snapshot publication remains the recovery and reconciliation mechanism for cache misses, initialization, and the optional periodic task.

`is_cache_ready()` checks the marker and every declared key as a DTO, without reading the database.
