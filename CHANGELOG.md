# Changelog

All notable changes to **Django-GC** are documented in this file.

## [Unreleased]

## [1.1.4] — 2026-09-11

### Changed

- `GlobalConfigCategory` now persists only its numeric ID. Category names and
  codes are code-owned presentation metadata resolved from
  `GLOBAL_CONFIG_CATEGORIES`.
- Django Admin now shows category codes and names as resolved read-only values;
  category filters and searches use the project definitions without persisting
  their presentation metadata.
- Initialization now raises an explicit `KeyError` when a
  `SettingDefinition.category_id` is missing from
  `GLOBAL_CONFIG_CATEGORIES`.

### Removed

- Removed the persisted `code`, `name`, `created_at`, and `updated_at`
  fields from `GlobalConfigCategory`. Migration `0002` removes the columns.

## [1.0.3] — 2026-09-06

### Changed

- Saving one `GlobalConfig` now refreshes only that typed cache entry under the
  shared refresh lock. Full snapshot rebuilds remain dedicated to cache misses,
  initialization, and the optional periodic task.

### Fixed

- An invalid or missing unrelated setting no longer prevents a successfully
  saved value from reaching cache through the post-commit callback.

## [1.0.2] — 2026-08-22

### Changed

- Physical table names are now `global_configs` and `global_config_categories`.
  The initial migration and docs match the model `db_table` values.

## [1.0.1] — 2026-08-22

### Added

- Initial library extract from the CPA GlobalConfig app: typed runtime keys,
  database-backed values, a full cache snapshot, initialization from project
  definitions, and stock Django Admin.
- Package metadata, Ruff, pre-commit, and pytest layout aligned with Django-Chassis.
- Single `GLOBAL_CONFIG_ENCRYPTION_KEY` setting for `SECURE` values. Categories,
  keys, and this encryption key are declared in the Django project's settings.

[1.1.4]: https://github.com/RDDLab/Django-GC/releases/tag/1.1.4
[1.0.3]: https://github.com/RDDLab/Django-GC/releases/tag/1.0.3
[1.0.2]: https://github.com/RDDLab/Django-GC/releases/tag/1.0.2
[1.0.1]: https://github.com/RDDLab/Django-GC/releases/tag/1.0.1
