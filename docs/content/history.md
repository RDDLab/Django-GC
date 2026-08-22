---
title: History
sidebar_position: 7
---

<Since v="1.0.1" />

Admin history is Django's built-in `LogEntry` journal. The package does not
depend on `django-simple-history`.

When an operator changes a value or a category name in Admin, Django records
who changed it and when. Open **History** on the object page to see those
entries.

`set_value()` is a programmatic write. It does not create an Admin `LogEntry`.
Projects that need an audit trail for service writes should record it in their
own domain log.

`SECURE` values are encrypted before `save()` when
`GLOBAL_CONFIG_ENCRYPTION_KEY` is set, so Admin history does not store a
newly typed secret in plaintext.
