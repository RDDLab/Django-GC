---
title: Cache
sidebar_position: 8
---

<Since v="1.0.1" />
<Changed v="1.0.1" />

The snapshot lives in Django's cache, alias `GLOBAL_CONFIG_CACHE_ALIAS` (default `default`).

| Key | Meaning | TTL |
|---|---|---|
| `global-config:{key}` | one typed DTO | none |
| `global-config:snapshot-ready` | full snapshot marker | none |
| `global-config:refresh-lock` | refresh lock | 30 seconds |

Lock wait timeout is 35 seconds. If the wait times out, the service accepts an already published snapshot or raises `GlobalConfigRefreshLockTimeoutError`. It never publishes without owning the lock.

Publish uses `cache.set_many`. On Redis/Valkey this is typically one `MSET`. Locmem is enough for tests and a single process.

`is_cache_ready()` checks the marker and every declared key as a DTO, without reading the database.
