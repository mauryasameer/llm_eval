# Task Tracker

Live progress tracker — always reflects actual state of in-flight work.

---

## Done

- [x] Align project structure with PROJECT_STANDARDS.md
  - [x] Copy standards file into repo (`.claude/PROJECT_STANDARDS.md`) and gitignore
  - [x] Create repo-level `CLAUDE.md`
  - [x] Add `VERSION`, `CHANGELOG.md`, `task.md`
  - [x] Add `pyproject.toml` with ruff config (replaces `pytest.ini`)
  - [x] Pin ruff in `requirements-dev.txt`
  - [x] Restructure into `src/` layout (core → src/services, providers, utils)
  - [x] Add abstract interfaces (`src/core/interfaces.py`)
  - [x] Reorganize `tests/` into `unit/`, `integration/`, `test_data/`
  - [x] Fix code quality issues (type annotations, top-level imports, `from __future__ import annotations`)
  - [x] Update CI: Python matrix (3.11+3.12) + lint job
  - [x] Update README: version badge + new structure section

---

## Backlog

- [ ] Pin `requirements.txt` to exact versions (pip freeze)
- [ ] Add `v0.1.0` git tag on main after alignment is merged
