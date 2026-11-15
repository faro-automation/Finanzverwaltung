# Finanzverwaltung

A small program to manage all bank accounts and cash reserves and assign them to purposes.

> Status: early planning. There is no functionality yet.

## Requirements

- Python 3.12
- On Debian/Ubuntu: `python3.12-venv`

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pre-commit install
```

## Checks

pre-commit runs ruff and mypy on every commit. To run all checks manually:

```bash
.venv/bin/ruff format .
.venv/bin/ruff check .
.venv/bin/mypy .
.venv/bin/pytest
```

The same checks run in CI on every pull request to `main` and `develop`.

## Dependencies

Direct dependencies are declared in `pyproject.toml`. Exact versions are locked with pip-tools:

```bash
.venv/bin/pip-compile --extra dev --strip-extras --output-file requirements-dev.txt pyproject.toml
.venv/bin/pip-sync requirements-dev.txt
```

## Project structure

```
src/      source code
tests/    tests
data/     local data (git-ignored, never committed)
```

## Branches

- `main`: deployable state
- `develop`: integration branch for development
- Working branches: `<type>/<description>`, branched from and merged back into `develop`

See `CHANGELOG.md` for the history of changes.

## License

[MIT](LICENSE). The software is provided "as is", without warranty or liability of any kind.
