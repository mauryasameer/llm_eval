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

- [x] meerax ecosystem infrastructure/governance parity — Docker (`docker compose run llm-eval python main.py --model <path> --eval all`), `GOVERNANCE.md`, committed the previously-untracked cross-tool config files (`.claude/`, `.cursorrules`, `AGENTS.md`, etc.), `.gitignore` fix for `reports/*.json`, README accuracy fixes (SHAP/LIME claim, adversarial-template count, HTML/PDF overstatement, clone-dir typo, Python version). No changes to accuracy/explainability/report logic — already more sophisticated than meerax's generic equivalents, so nothing there was replaced.

## Backlog

- [ ] Pin `requirements.txt` to exact versions (pip freeze)
- [ ] `TorchSaliencyProvider.compute()` silently falls back to `np.random.rand()` — fabricated random saliency data — on ANY exception from the real attention-extraction path, and this fallback is live in production code, not just test-guarded. A compliance-facing explainability tool that can silently hand a reviewer fake data dressed up as real output is a real integrity risk. Needs its own fix: either raise/surface the failure instead of fabricating data, or clearly flag in the report when the fallback path was used.
- [ ] `report_metadata`'s `evaluator` and `standards_mapped` fields (populated in `main.py`) are never actually rendered anywhere in `reports/templates/report_template.html` — dead metadata. Either render them or stop populating them.
- [ ] `transparency_score` is configured in `configs/regulatory_mapping.yaml` (with a real `conflicts_with` pairing against `pii_masking_rate`) but is never actually computed by `main.py`'s real eval flow — meaning `ConflictResolver`'s regulatory-paradox detection can currently only ever trigger in `report_service.py`'s own mock/`__main__` demo data, never in a real evaluation run.
