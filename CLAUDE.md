# Claude Instructions for llm_eval

## Engineering Standards

All work on this project must follow the conventions defined in `.claude/PROJECT_STANDARDS.md`.

That file is the single source of truth for:
- Repository layout (`src/` structure, provider abstraction pattern)
- Branching and commit conventions
- Semantic versioning and CHANGELOG format
- Lint tooling (ruff + `pyproject.toml`)
- Testing layout (`tests/unit/`, `tests/integration/`, `tests/test_data/`)
- Python coding standards (modern type annotations, top-level imports, logging over print)

Read `.claude/PROJECT_STANDARDS.md` before making any structural or architectural change.

## Project-Specific Rules

- This is a financial compliance evaluation framework — changes to evaluator logic must preserve regulatory traceability (SR 11-7, EU AI Act, GDPR mappings in `configs/regulatory_mapping.yaml`).
- Never commit ML model weights or HuggingFace cache files.
- All PRs must target `dev`, never `main` directly.
