---
title: Типы
sidebar_position: 5
---

<Since v="1.0.1" />

<Changed v="1.1.0" />

`SettingType` — `IntEnum` с `ChoicesEnumMixin`. Члены — целые числа (`STRING = 0`). Подписи в `label()`. Поля Django берут `SettingType.choices()`. В базе всегда текст (или `NULL`). Сервис преобразует снимок к типизированным значениям.

| Тип | Формат хранения | Runtime |
|---|---|---|
| `STRING` | текст | `str` |
| `BOOLEAN` | `True` / `true` / `1` / `yes` | `bool` |
| `INTEGER` | цифры | `int` |
| `FLOAT` | десятичный текст | `float` |
| `DECIMAL` | десятичный текст | `Decimal` |
| `SECURE` | зашифрованный текст | расшифрованный `str` |
| `DATE` | `DD.MM.YYYY` | `date` |
| `TIME` | `HH:MM:SS` | `time` |
| `DATETIME` | `DD.MM.YYYY HH:MM:SS` | aware `datetime` |
| `STRING_ARRAY` | `a;b;c` | `list[str]` |
| `INTEGER_ARRAY` | `1;2;3` | `list[int]` |
| `FLOAT_ARRAY` / `DECIMAL_ARRAY` | через точку с запятой | `list[float]` / `list[Decimal]` |
| `*_CHOICES` | выбранное значение | типизированный скаляр |
| `*_MULTIPLE_CHOICES` | JSON-список | `list` |
| `JSON` | JSON или Python-литерал | разобранный объект |
| `UUID` | текст UUID | `UUID` |
| `COLOR` | не используется | ошибка разбора |

JSON сначала читается через `json.loads`. Python-литерал с одинарными кавычками — запасной путь. Подмена `'` на `"` не используется: она ломает валидный JSON с апострофом.
