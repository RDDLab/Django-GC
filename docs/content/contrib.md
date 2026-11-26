---
title: Contribution Guide
sidebar_position: 11
---

We welcome contributions to Django-GC. This guide covers the local
workflow for development, testing, and documentation.

If you are not sure whether a change fits the project, open an issue or a
draft pull request first.

Please keep changes focused and include tests when behavior changes.

## Setting up environment

The project uses `uv` for Python dependency management. To install it, follow
the official guide in the
[uv documentation](https://docs.astral.sh/uv/getting-started/installation/).

After cloning the repository, install dependencies:

```bash
uv sync --locked --group dev
```

## Linting

Ruff reads `ruff.toml`: line length 120, project ignore list, and
`force-exclude` for migrations and Markdown. Do not run Ruff without that
file — the defaults fight Django admin class attrs and docs examples.

```bash
uv run ruff check --config ruff.toml .
uv run pyrefly check
```

Use Ruff as a linter in pre-commit. Omit optional trailing commas in imports,
collections, calls, and signatures. Put each name in a nonempty `__all__` list
on its own line and keep the declared export order.

## Testing

```bash
bash .github/scripts/compile-translations.sh
uv run --locked pytest
```

## Working with documentation

Documentation is built with [Docusaurus](https://docusaurus.io/). The site
is bilingual (English source, Russian mirrors) and is **not** versioned.
Public API is marked with `<Since v="x.y.z" />` badges instead.

```bash
cd docs
npm install --global "$(node -p 'require("./package.json").packageManager')"
npm ci
npm run docs:dev
```

English is the default locale at `/` — there is no `/en/` prefix. Russian is
the i18n overlay at `/ru/`. `docs:dev` serves English on port 3100, Russian
on 3101 (under `/ru/`), and proxies `/ru` from the English server so the
locale dropdown can switch both ways. Ports differ from Django-Chassis
(3000/3001) so both sites can run at once. Use `docs:dev`, not
`docs:dev:ru` alone, if you need to switch languages.

```bash
npm run docs:typecheck
npm run docs:build
npm run docs:serve
```

## CI, releases and deployment

Pushes to any branch and pull requests run security checks. On a push to `main`, security checks and tests appear in a single CI run, with tests starting after the scans pass. For other branches, a successful push scan starts testing only for the current head of a protected branch. Manual test runs are available under **Actions**.

The test pipeline uses the dependency lock, verifies the Django migration state, runs the Python and Django matrix, builds both Python distributions and verifies the English and Russian documentation. The security workflow scans secrets, Python, Django templates, documentation JavaScript and TypeScript, and workflow files. It audits locked Python and npm dependencies.

The release workflow scans the release revision, verifies it matches the current head of `main` and requires a successful `testing.yml` run for that exact SHA on `main`. Publish only after the test run finishes. Run manual publishing from `main`. After uploading wheel and sdist to PyPI, the workflow dispatches the documentation workflow for the published commit. The documentation workflow checks ancestry and reuses the test result for the selected revision before deploying over SSH. The documentation workflow uses the `docs-production` environment to install the deployment files in the SSH user’s home directory. The deploy job streams the selected source archive to the server, and the SSH account builds it with Docker. If the container fails its health check, the deployment script restores the previous image and port.

[Set up the GitHub environment and the documentation server](https://github.com/RDDLab/Django-GlobalConfig/blob/main/.github/docs/README.md).

## Version badges

Any new public setting, type, or extra must be marked in **both** languages:

```mdx
<Since v="1.1.0" />
```

Behaviour or signature changes use `<Changed v="..." />` and a
`CHANGELOG.md` entry. The badge version is the package version that first
shipped the feature, not a documentation version.

## Project conventions

- **Full typing** — annotate every function parameter, return value, and
  variable. The project targets `pyrefly` strict mode.
- **No relative imports** — always use absolute imports
  (`from django_gc.services import get_value`).
- **Keyword arguments** — pass arguments by keyword where possible.
- **`uv run`** — run Python commands as `uv run pytest`, not bare `python`.
- Runtime code reads and writes through `get_value()` / `set_value()`, not the ORM.
- Domain keys live in a project `StrEnum` and are passed into those calls.
- English and Russian docs stay in sync.
- Public API changes need a `CHANGELOG.md` entry.
