# Changelog

All notable changes to **Django-GC** are documented in this file.

## [Unreleased]

### Changed

- Renamed the project to Django-GC. The Python package is `django_gc` and
  the PyPI name is `django-gc`.
- Renamed Django settings `GLOBAL_SETTINGS_*` to `GLOBAL_CONFIG_*`
  (`CATEGORIES`, `DEFINITIONS`, `ENCRYPTION_KEY`, `CACHE_ALIAS`).
- Renamed public `GlobalSetting*` types to `GlobalConfig*`
  (`GlobalConfig`, `GlobalConfigCategory`, exceptions, services, and the
  Celery task). `SettingDefinition` and `SettingType` are unchanged.
- Set explicit table names: `global_config` and `global_config_category`.
- `SettingType` is now `IntEnum` with `ChoicesEnumMixin` instead of Django
  `IntegerChoices`. Use `SettingType.choices()` and `member.label()`.

## [1.0.1] — 2026-08-22

### Added

- Initial library extract from the CPA GlobalConfig app: typed runtime keys,
  database-backed values, a full cache snapshot, initialization from project
  definitions, and stock Django Admin.
- Package metadata, Ruff, pre-commit, and pytest layout aligned with Django-Chassis.
- Single `GLOBAL_CONFIG_ENCRYPTION_KEY` setting for `SECURE` values. Categories,
  keys, and this encryption key are declared in the Django project's settings.

[1.0.1]: https://github.com/RDDLab/Django-GC/releases/tag/1.0.1
