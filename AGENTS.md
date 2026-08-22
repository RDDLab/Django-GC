# Django-GC agent notes

Typed Django runtime configuration: code-declared keys, database-backed values,
a full cache snapshot, and stock Django Admin. Domain keys stay in the project.

Documentation: https://django-gc.rdd-lab.com/

## Working in this repo

- Use `uv run` for Python commands (`uv run pytest`, `uv run ruff check .`).
- Full typing, `pyrefly` strict. Absolute imports only.
- Pass arguments by keyword where possible.
- Runtime code must read values through `get_value()`, not the ORM.
- Add tests when behaviour changes.
- Public API changes need a `CHANGELOG.md` entry.
- Any change must update the documentation. English (`docs/content/`) and
  Russian (`docs/i18n/ru/docusaurus-plugin-content-docs/current/`) stay in
  sync. Examples must match the code. New or changed public options,
  settings, and extras also need `<Since />` / `<Changed />` badges.

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
