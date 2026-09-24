# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.3] - 2026-09-24

### Changed
- Added a repository hero that illustrates the framework's financial-services LLM validation, evidence, and regulatory traceability workflow.

## [0.3.2] - 2026-09-15

### Removed
- `CLAUDE.md` — the most visibly AI-tool-branded file remaining (root-level, named after
  Claude). Its genuinely useful, non-tool-specific project rules (regulatory-traceability
  requirement on evaluator changes, never committing model weights/HF cache) were folded
  into `CONTRIBUTING.md`, which already covered the dev-branch-only PR policy.

### Fixed
- `CONTRIBUTING.md` step 3 referenced a stale `core/evaluators/` path — the real location
  for new evaluator modules is `src/services/`.

## [0.3.1] - 2026-09-15

### Removed
- `.claude/`, `.cursorrules`, `.mcp.json`, `.opencode.json`, `.windsurfrules`, `AGENTS.md`,
  `GEMINI.md` were committed in v0.3.0 — removed from tracking and gitignored. Regardless
  of their content (mostly operational tooling config, not planning documents), files or
  directories named after specific AI coding tools have no place in a public repo.

## [0.3.0] - 2026-09-15

### Added
- `Dockerfile`/`docker-compose.yml` for the evaluation CLI (`main.py`), targeting the
  torch/transformers backend since `mlx-lm` is Apple-Silicon-only. `--model` is a required
  CLI argument with no universal default, so the container's default command shows
  `--help` — a real run is `docker compose run llm-eval python main.py --model <path>
  --eval all`.
- `GOVERNANCE.md` — intended use, explainability boundary, fairness scope, LLM controls,
  audit trail, regulatory framing.
- Guarded `docker compose config` validation job in CI.
- Committed several previously-untracked, load-bearing cross-tool config files:
  `.claude/`, `.cursorrules`, `.mcp.json`, `.opencode.json`, `.windsurfrules`, `AGENTS.md`,
  `GEMINI.md`.

### Fixed
- README claimed the Explainability module uses SHAP/LIME — it doesn't; it computes
  attention-based token saliency directly from the final transformer layer's attention
  weights. Corrected in both the System Architecture and Explainability Auditor sections.
- README overstated the adversarial test library as "50+ templates" — the test file
  actually wired into `main.py`'s default `--adversarial-tests` path has a small, curated
  set; a larger `jailbreaks.json` exists but isn't wired in by default.
- README claimed "HTML/PDF" report output — `report_service.py` only generates HTML.
- README's clone instructions had a directory-name typo (`cd llm-eval-framework` after
  cloning into `llm_eval/`).
- README's prerequisites listed "Python 3.11+" — the actual target is 3.12
  (`pyproject.toml`'s `target-version`).
- `.gitignore` was missing a rule for `reports/*.json` (generated run output), unlike the
  adjacent `reports/*.html` and `reports/plots/*.png` rules.

### Known issues (tracked in `task.md`, not fixed this release)
- `TorchSaliencyProvider.compute()` silently fabricates random saliency data on any
  exception from the real attention-extraction path — a real integrity risk in a
  compliance-facing explainability tool, deliberately deferred rather than fixed
  alongside this infrastructure work.
- `report_metadata`'s `evaluator`/`standards_mapped` fields are populated but never
  rendered in the report template.
- `transparency_score` is configured with a real `conflicts_with` regulatory pairing but
  is never computed by the live eval flow, so paradox detection can currently only trigger
  in mock/demo data.

## [0.2.0] - 2026-04-13

### Changed
- Upgraded CI to Python 3.12 (single version, removed 3.11/3.12 matrix)
- Updated ruff `target-version` to `py312` in `pyproject.toml`

### Added
- `code-review-graph==2.2.1` to dev dependencies for local knowledge graph (6-8x token savings)

## [0.1.0] - 2026-04-04

### Added
- Initial release of LLM Evaluation & Validation Framework for Financial Services
- `FinancialNormalizer` and `evaluate_financial_f1` for weighted entity-level F1 scoring
- `evaluate_safety` adversarial prompt injection evaluator
- Attention-based saliency explainability module (MLX + PyTorch backends)
- Jinja2 HTML report generator with audit trail
- `ConflictResolver` for detecting regulatory paradoxes (SR 11-7 vs EU AI Act vs GDPR)
- `RegulatoryMapper` for YAML-driven metric-to-control mapping
- Gradio web UI deployed to HuggingFace Spaces
- Google Colab demo notebook
- GitHub Actions CI (pytest) and HuggingFace Space deploy workflows

[0.1.0]: https://github.com/mauryasameer/llm_eval/releases/tag/v0.1.0
[0.3.3]: https://github.com/mauryasameer/llm_eval/compare/v0.3.2...v0.3.3
