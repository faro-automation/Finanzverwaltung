# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Project rules for Claude Code in `CLAUDE.md`
- Development tooling: ruff, mypy (strict), pytest, pre-commit, pip-tools
- CI workflow running all checks on pull requests to `main` and `develop`
- Folder structure with `src/`, `tests/` and git-ignored `data/`
- MIT license
- Domain model in `finance_manager.model`:
  - `UserConfig` for per-user counters and unique Topf names
  - `Currency` and `Value` (signed money value, never `float`), `Month`
  - Geldorte: `Bankkonto` (with `Kontoart`), `Bargeld`, `Gutscheine`, each with a
    unique identifier, an actual value and an active/closed status
  - `Topf` with a main Geldort, values per Geldort and an active/dissolved status
  - Transactions: `RealTransaction` (with identifier, statement text, direction and
    Auslage/Rückzahlung mark) and `TopfTransfer`
  - `Auslage` with an expected number of Rückzahlungen
  - `SalaryPlan` with `Salary`, remainder Topf, valid-from month and an allocation
    of `SalaryPart`s made of named `SalaryPartItem`s; every change is checked so
    that the allocation never exceeds the salary

### Changed

- ruff no longer limits the number of function parameters
