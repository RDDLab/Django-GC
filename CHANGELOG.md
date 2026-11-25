# Changelog

All notable changes to **Django-GC** are documented in this file.

## [Unreleased]

## [1.1.5] — 2026-11-26

### Added

- Support Python 3.15 with Django 6.1.3 and later. Verify Django 6.0 and locked Django on Python 3.12–3.14.
- Add hosted CI with source and dependency scans, package and bilingual documentation builds, and SSH deployment of the documentation.

- Providers connect categories, setting definitions, validation, access rules and protected editors owned by integrating projects and libraries.
- Add the explicit `initialize_global_configs` command. It creates missing keys and categories, moves values from declared `previous_keys` and preserves existing canonical values.
- Add typed writes, fresh reads of one or several keys, and ordered locks for settings updated in a transaction.
- Package the standard Django Admin templates and translated setting metadata.
- Ship English and Russian translation catalogs for admin labels, form validation, and initialization messages.

### Changed

- Validate new keys as `<namespace>.<snake_case>` and detect conflicts in namespaces, categories and keys.
- Show the active definitions in the settings catalog. Retired keys stay in the database for rollback and are excluded from the runtime cache.
- Allow lists and scalar values in JSON fields. Protect read-only metadata and mask secrets in the admin.
- Combine provider view and edit permissions with Django Admin permissions. Execute owner signal handlers in the model save transaction.
- Export the runtime API for use from settings before Django loads the models.
- Document cache reads, typed writes, provider hooks, and initialization in English docstrings.

### Fixed

- Recognize unchanged numeric values in the standard settings form.

### Removed

- Remove automatic initialization on `post_migrate`. Run `initialize_global_configs` after migrating the schema and when definitions change.

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

[1.1.4]: https://github.com/RDDLab/Django-GlobalConfig/releases/tag/1.1.4
[1.0.3]: https://github.com/RDDLab/Django-GlobalConfig/releases/tag/1.0.3
[1.0.2]: https://github.com/RDDLab/Django-GlobalConfig/releases/tag/1.0.2
[1.0.1]: https://github.com/RDDLab/Django-GlobalConfig/releases/tag/1.0.1

[Unreleased]: https://github.com/RDDLab/Django-GlobalConfig/compare/1.1.5...HEAD
[1.1.5]: https://github.com/RDDLab/Django-GlobalConfig/compare/1.1.4...1.1.5
