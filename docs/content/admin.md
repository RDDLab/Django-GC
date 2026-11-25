---
title: Admin
sidebar_position: 6
---

<Since v="1.0.1" />
<Changed v="1.1.4" />

Django-GC uses the standard Django Admin list and edit page. Provider permissions determine which rows are visible.

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

Numeric forms compare the submitted number to the stored value.

Read-only keys disable the value field. Required keys cannot be saved empty.

<Changed v="1.1.5" />

The catalog shows description, value, type, key and category. SECURE values are masked. Only the value is editable; read-only values are also protected server-side. Integrating projects may open the owner editor in a Chassis modal while retaining owner checks and confirmation.

The wheel includes `admin/django_gc/configuration_metadata.html` for integrations using the standard Django template loader. Projects can extend the standard edit form to add their own modal.

## Languages

Django-GC ships English and Russian translations for its admin labels, setting
types, validation messages and initialization command. It uses Django's active
language and uses the English source text when a translation is unavailable.
To let users switch between English and Russian, enable both languages in the
project's `LANGUAGES` and configure Django's `LocaleMiddleware`.

Projects and providers supply translations for their own setting descriptions,
category names and choice labels. Declare those strings in the owning
application's message catalog. Run `bash .github/scripts/compile-translations.sh`
before testing translations from a checkout. Published wheels include the
compiled Django-GC catalogs.
