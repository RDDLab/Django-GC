---
title: Types
sidebar_position: 5
---

<Since v="1.0.1" />

<Changed v="1.1.0" />

`SettingType` is an `IntEnum` with `ChoicesEnumMixin`. Members are integers (`STRING = 0`). Labels live on `label()`. Django fields use `SettingType.choices()`. The database always stores text (or `NULL`). The service converts the snapshot to typed values.

| Type | Stored format | Runtime value |
|---|---|---|
| `STRING` | text | `str` |
| `BOOLEAN` | `True` / `true` / `1` / `yes` | `bool` |
| `INTEGER` | digits | `int` |
| `FLOAT` | decimal text | `float` |
| `DECIMAL` | decimal text | `Decimal` |
| `SECURE` | encrypted text | decrypted `str` |
| `DATE` | `DD.MM.YYYY` | `date` |
| `TIME` | `HH:MM:SS` | `time` |
| `DATETIME` | `DD.MM.YYYY HH:MM:SS` | aware `datetime` |
| `STRING_ARRAY` | `a;b;c` | `list[str]` |
| `INTEGER_ARRAY` | `1;2;3` | `list[int]` |
| `FLOAT_ARRAY` / `DECIMAL_ARRAY` | semicolon-separated | `list[float]` / `list[Decimal]` |
| `*_CHOICES` | selected value | typed scalar |
| `*_MULTIPLE_CHOICES` | JSON list | `list` |
| `JSON` | JSON or a Python literal | parsed object |
| `UUID` | UUID text | `UUID` |
| `COLOR` | unused | parse error |

JSON first uses `json.loads`. A Python literal with single quotes is the fallback. Replacing `'` with `"` is not used: it breaks valid JSON that contains an apostrophe.
