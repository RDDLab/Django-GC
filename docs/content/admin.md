---
title: Admin
sidebar_position: 6
---

<Since v="1.0.1" />
<Changed v="1.1.4" />

Admin is stock Django. There is no Tabler dependency.

`GlobalConfigAdmin` and `GlobalConfigCategoryAdmin` register on
`admin.site` as standard `ModelAdmin` classes. Admin history is Django
`LogEntry`.

- add and delete permissions are always false
- keys, types, descriptions, and numeric categories are read-only
- category labels and filter choices are resolved from `GLOBAL_CONFIG_CATEGORIES`
- the category page shows the persisted ID and resolved code/name as read-only values
- `list_filter` covers the resolved category, type, and read-only
- search covers key, description, and category definition code/name

The change form picks a widget from `SettingType`: HTML5 date/time inputs, password input for `SECURE`, semicolon arrays, and checkbox multiple choice.

Read-only keys disable the value field. Required keys cannot be saved empty.
