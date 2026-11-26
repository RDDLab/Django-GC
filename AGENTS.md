# Django-GC agent notes

Typed Django runtime configuration: code-declared keys, database-backed values,
a full cache snapshot, and stock Django Admin. Domain keys stay in their owning project or library provider.

Documentation: https://django-gc.rdd-lab.com/

## Working in this repo

- Use `uv run` for Python commands (`uv run pytest`, `uv run ruff check .`).
- Full typing, `pyrefly` strict. Absolute imports only.
- Pass arguments by keyword where possible.
- Use Ruff for linting only. Keep the formatter out of pre-commit.
- Omit optional trailing commas in imports, collections, calls, and signatures.
- Write every name in a nonempty `__all__` list on its own line. Keep the
  declared export order and omit the optional comma after the last name.
- Runtime code must read values through `get_value()`, not the ORM.
- Add tests when behaviour changes.
- Public API changes need a `CHANGELOG.md` entry.
- Any change must update the documentation. English (`docs/content/`) and
  Russian (`docs/i18n/ru/docusaurus-plugin-content-docs/current/`) stay in
  sync. Examples must match the code. New or changed public options,
  settings, and extras also need `<Since />` / `<Changed />` badges.

## Documentation deployment

- Configure `DOCS_IP` on `docs_net` and connect the reverse proxy to the
  container's internal port `8080` without publishing a host port.

## Documentation version badges

Docs are bilingual. English is the default locale at `/` (`docs/content/`).
Russian is the i18n overlay at `/ru/`
(`docs/i18n/ru/docusaurus-plugin-content-docs/current/`). There is no
Docusaurus versioning.

Any new public setting, type, or extra must be marked in **both** languages:

```mdx
<Since v="1.1.0" />
```

Behaviour or signature changes use `<Changed v="..." />`. The badge version
is the package version that first shipped the feature.

Keep English and Russian pages in sync. Examples must match the code.

Настройки библиотеки объявляются в её собственном ConfigurationProvider и подключаются проектом через GLOBAL_CONFIG_PROVIDERS. GC не импортирует MFA/OIDC/Chassis и не содержит их предметных ключей. Проект назначает ID категорий и владеет своими определениями; общий каталог не дублирует значения в таблицах библиотек. Параметры запуска (INSTALLED_APPS, URL, backend, подключения и секреты) остаются в Django settings, поскольку нужны до доступности GC. Сущности, факторы и транзакционное состояние не превращаются в настройки.

Категории и ключи GC создаются только явной командой initialize_global_configs из django-gc. Миграции создают схему; post_migrate, startup и system checks не инициализируют значения. Повторный запуск команды сохраняет рабочие значения и переносит прежнее значение только для отсутствующего ключа.


Ключи GC имеют единственный формат `<namespace>.<snake_case>`: строчные латинские буквы, цифры и подчёркивания, одна точка между пространством владельца и именем. Примеры: `mfa.admin_totp_digits`, `oidc.admin_http_timeout_seconds`, `chassis.navbar_position`, `project.name`, `risk.is_enabled`. Старые имена объявляются явно в `SettingDefinition.previous_keys` и переносятся только командой `initialize_global_configs`; существующее каноническое значение имеет приоритет. Старые строки сохраняются для отката и не участвуют в рабочем кэше. Идентификаторы протоколов, enum и подписанных снимков не переименовываются вместе с ключами GC.

Глобальные параметры MFA/OIDC сохраняются обычной формой GC без предварительной проверки и отдельного подтверждения в модальном окне. До SQL-записи проверяются тип, диапазон, границы доверия и права владельца. Сигналы только объявленных ключей после записи проверяют совместимость в той же транзакции. GC хранит желаемое значение; RuntimeConfiguration библиотеки — сущность последней проверенной активации, не второй редактор настроек. При ошибке новое значение остаётся в GC, рабочий снимок сохраняется и защита входа не отключается. Ошибка показывается через global_alert со ссылкой на защищённую диагностику; исправление снимает уведомление. Кэш сбрасывается после commit, рабочая версия хранится в базе. Политики как сущности сохраняют свой сценарий подтверждения. Прямой SQL/bulk update не является поддерживаемым способом изменения настроек.

## Стандартный Django UI

- Поставлять единственные стандартные Django-шаблоны в `templates/` и ресурсы в `static/`.
- Дизайн Django Admin с дополнениями Chassis сверять с опубликованным v1.0.22. Новые options и компоненты
  оформлять в том же стиле. Сохранять контракты форм, маршрутов, прав и действий.
- Проекты переопределяют шаблоны и подключают собственные ресурсы через штатные загрузчики Django.
  Переопределения Tabler для Angie Proxy Manager принадлежат приложению `apps.ui` проекта.
