---
title: Admin
sidebar_position: 6
---

<Since v="1.0.1" />
<Changed v="1.0.1" />

Admin is stock Django. There is no Tabler dependency.

`GlobalConfigAdmin` and `GlobalConfigCategoryAdmin` register on `admin.site` as standard `ModelAdmin` classes. Admin history is Django `LogEntry`.

- add and delete permissions are always false
- keys, types, descriptions, and category codes are read-only
- operators can change a value and a category display name
- `list_filter` covers category, type, and read-only
- search covers key, description, category code, and name

The change form picks a widget from `SettingType`: HTML5 date/time inputs, password input for `SECURE`, semicolon arrays, and checkbox multiple choice.

Read-only keys disable the value field. Required keys cannot be saved empty.
