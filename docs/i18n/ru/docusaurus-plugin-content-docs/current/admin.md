---
title: Admin
sidebar_position: 6
---

<Since v="1.0.1" />
<Changed v="1.1.4" />

Admin — стандартный Django. Зависимости от Tabler нет.

`GlobalConfigAdmin` и `GlobalConfigCategoryAdmin` регистрируются на
`admin.site` как обычные `ModelAdmin`. История Admin — Django `LogEntry`.

- права add и delete всегда ложны
- ключи, типы, описания и числовые категории только для чтения
- подписи категорий и варианты фильтра берутся из `GLOBAL_CONFIG_CATEGORIES`
- страница категории показывает сохранённый ID и вычисленные code/name только для чтения
- `list_filter` покрывает разрешённую категорию, тип и read-only
- поиск покрывает ключ, описание, код и название категории из definitions

Форма выбирает виджет по `SettingType`: HTML5 date/time, password для `SECURE`, массивы через точку с запятой и checkbox для множественного выбора.

Read-only ключи блокируют поле значения. Обязательные ключи нельзя сохранить пустыми.
