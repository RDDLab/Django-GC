---
title: Кэш
sidebar_position: 8
---

<Since v="1.0.1" />
<Changed v="1.0.1" />

Снимок живёт в Django cache, алиас `GLOBAL_CONFIG_CACHE_ALIAS` (по умолчанию `default`).

| Ключ | Смысл | TTL |
|---|---|---|
| `global-config:{key}` | один типизированный DTO | нет |
| `global-config:snapshot-ready` | маркер полного снимка | нет |
| `global-config:refresh-lock` | блокировка refresh | 30 секунд |

Ожидание lock — 35 секунд. Если timeout, сервис принимает уже опубликованный снимок или бросает `GlobalConfigRefreshLockTimeoutError`. Публикация без владения lock запрещена.

Публикация идёт через `cache.set_many`. На Redis/Valkey это обычно один `MSET`. Locmem достаточно для тестов и одного процесса.

`is_cache_ready()` проверяет маркер и каждый объявленный ключ как DTO, без чтения базы.
