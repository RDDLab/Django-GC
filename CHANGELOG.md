# Changelog

All notable changes to **Django-GC** are documented in this file.

## [Unreleased]

## [1.0.1] — 2026-08-22

### Added

- Initial library extract from the CPA GlobalConfig app: typed runtime keys,
  database-backed values, a full cache snapshot, initialization from project
  definitions, and stock Django Admin.
- Package metadata, Ruff, pre-commit, and pytest layout aligned with Django-Chassis.
- Single `GLOBAL_CONFIG_ENCRYPTION_KEY` setting for `SECURE` values. Categories,
  keys, and this encryption key are declared in the Django project's settings.

[1.0.1]: https://github.com/RDDLab/Django-GC/releases/tag/1.0.1
