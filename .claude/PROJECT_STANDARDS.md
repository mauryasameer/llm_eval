# Project Standards & Engineering Practices

This document captures the engineering conventions, branching strategy, versioning rules, and coding standards established while building this project. Use it as a reference when starting or continuing any Python project.

---

## 1. Repository Structure

Every project should have this baseline layout before writing a single line of feature code:

```
project_name/
├── src/
│   ├── core/               # Abstract interfaces only — no implementations
│   ├── providers/          # Concrete implementations of core interfaces
│   ├── services/           # Business logic — orchestrates providers
│   ├── utils/              # Stateless helper functions
│   └── data/               # Runtime storage (git-ignored)
├── tests/
│   ├── unit/               # One file per service/provider
│   ├── integration/        # End-to-end tests with stubs for external deps
│   └── test_data/          # Fixture files (CSV, JSON, SQLite samples)
├── scripts/                # One-off utilities, data generators
├── .github/
│   └── workflows/
│       └── ci.yml          # CI: tests + lint on every push
├── conftest.py             # sys.path setup so `from src.* import *` works everywhere
├── pyproject.toml          # Single source of truth for ruff config
├── requirements.txt        # Pinned exact versions (pip freeze output)
├── VERSION                 # Single line: the current version string (e.g. 0.4.3)
├── CHANGELOG.md            # Keep a Changelog format
├── task.md                 # Live progress tracker — always reflects actual state
└── README.md               # User-facing doc — kept in sync with code on every release
```

Key rules:
- `src/data/` is **always** git-ignored. Runtime databases, vector stores, and caches live here.
- `conftest.py` at root level inserts `src/` into `sys.path` so tests use the same import paths as the app.
- Never scatter config across multiple files. Linting config goes in `pyproject.toml`. Dependency pins go in `requirements.txt`. Nothing else.

---

## 2. Provider Abstraction Pattern

Every external dependency (LLM, vector DB, email provider, PII masker) gets an abstract interface defined in `src/core/interfaces.py` before any implementation is written.

```python
# src/core/interfaces.py
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, system_prompt: str | None = None) -> str: ...

    @abstractmethod
    def classify_email(self, email_data: dict, context: str | None = None) -> ClassificationResult: ...
```

Concrete implementations live in `src/providers/`:
- `ollama_provider.py` implements `LLMProvider` using local Ollama
- `openai_provider.py` implements the same interface using the OpenAI API
- Swapping providers is one constructor argument change — no service code changes

This pattern is non-negotiable. It makes the system testable (mock the interface, not the HTTP call), extensible (add a new provider without touching services), and prevents vendor lock-in.

---

## 3. Agile SDLC & Branching Strategy

### Branch hierarchy (strict — never skip levels)

```
feature/* or fix/*
        ↓
       dev          ← primary integration branch
        ↓
      main          ← production-stable, tagged on every release
```

### Rules

| Rule | Detail |
|---|---|
| **Never commit directly to `main` or `dev`** | Always branch from `dev`, work on `feature/*` or `fix/*`, then PR back |
| **`main` gets tagged on every merge** | `git tag v0.4.3 && git push origin v0.4.3` |
| **All tests must pass before merging to `dev`** | `pytest tests/ -v` — zero failures, no skips |
| **Lint must pass before merging to `dev`** | `ruff check .` — zero issues |
| **Commit messages use imperative mood** | "feat: add Outlook connector" not "added outlook" |

### Commit prefix conventions

| Prefix | When to use |
|---|---|
| `feat:` | New user-facing functionality |
| `fix:` | Bug fix |
| `chore:` | Config, CI, dependency updates |
| `refactor:` | Code restructuring with no behavior change |
| `test:` | Test additions or corrections |
| `release:` | Version bump + changelog entry |

### Branch naming

```
feature/short-description       # new capability
fix/short-description           # bug or lint fix
release/v0.5                    # optional staging branch before main merge
```

---

## 4. Versioning

Follow **Semantic Versioning** (`MAJOR.MINOR.PATCH`):

| Increment | When |
|---|---|
| PATCH (`0.4.x`) | Bug fixes, lint fixes, doc corrections, CI fixes |
| MINOR (`0.x.0`) | New features that are backward-compatible |
| MAJOR (`x.0.0`) | Breaking changes to interfaces or data schema |

### Version files

- `VERSION` — single line, the current version string. Read by `src/app.py` at startup.
- `CHANGELOG.md` — one entry per version, Keep a Changelog format.
- `README.md` — version badge at top, updated on every MINOR or MAJOR bump.

### CHANGELOG format

```markdown
## [0.4.3] - 2026-04-04
### Fixed
- Short, factual description of what was broken and what was changed

## [0.4.2] - 2026-04-03
### Added
- ...

[0.4.3]: https://github.com/owner/repo/compare/v0.4.2...v0.4.3
[0.4.2]: https://github.com/owner/repo/compare/v0.4.1...v0.4.2
```

Every entry must have a comparison link at the bottom of the file. Use `Added`, `Changed`, `Fixed`, `Removed` sections — never mix them in one bullet.

---

## 5. Lint & Code Quality

### Tool: ruff

Single config in `pyproject.toml` — CI reads from it, local dev reads from it. Never inline flags in CI commands.

```toml
[tool.ruff]
target-version = "py311"
line-length = 120

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "UP",   # pyupgrade — modernise Python syntax
    "B",    # bugbear — common bug patterns
    "PIE",  # miscellaneous improvements
    "PLC",  # pylint convention
]
ignore = [
    "E501",   # long lines — intentional in prompt strings
    "B008",   # function call in default argument
    "UP007",  # keep Optional in public API signatures
    "PIE790", # unnecessary pass in abstract stubs
]

[tool.ruff.lint.per-file-ignores]
"scripts/*" = ["PLC0415", "T201"]
"tests/*"   = ["S101", "PLC0415"]
"conftest.py" = ["PLC0415"]
```

### Pin ruff in requirements.txt and CI identically

```txt
# requirements.txt
ruff==0.15.9
```

```yaml
# .github/workflows/ci.yml
- name: Install linting tools
  run: pip install ruff==0.15.9
```

A version mismatch between local and CI ruff will cause rules to behave differently. Pin both to the same version.

### Common ruff pitfalls

| Issue | Fix |
|---|---|
| `UP006`: `List[str]` / `Dict[str, Any]` | Use `list[str]` / `dict[str, Any]` (Python 3.9+) |
| `UP045`: `Optional[X]` | Use `X \| None` |
| `UP017`: `timezone.utc` | Use `datetime.UTC` (Python 3.11+) |
| `UP038`: `isinstance(x, (int, float))` | Use `isinstance(x, int \| float)` — ruff won't auto-fix this; do it manually |
| `PLC0415`: import inside function | Move all imports to module top-level |
| `I001`: unsorted imports | Run `ruff check --fix` to auto-sort |
| Trailing whitespace in string literals | ruff cannot fix these — use `sed -i '' 's/[[:space:]]*$//' file.py` |
| Invalid return type annotation `-> (str, bool)` | Must be `-> tuple[str, bool]` |

### CI workflow structure

```yaml
jobs:
  test:
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip
      - run: pip install -r requirements.txt
      - run: pytest tests/unit/ -v --tb=short
      - run: pytest tests/integration/ -v --tb=short

  lint:
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
      - run: pip install ruff==<pinned-version>
      - run: ruff check .
```

---

## 6. Testing Standards

### Structure

- One test file per service or provider: `tests/unit/test_masking.py`, `tests/unit/test_rag.py`
- Integration tests use stubs for all external dependencies (LLM, vector DB, email API) — no real HTTP calls in CI
- Fixture files (`tests/test_data/`) contain minimal, representative samples (3-5 rows is enough)

### Rules

- Every new service ships with its unit tests in the same branch — not a separate PR
- Test the behavior, not the implementation. Verify outputs, not internal method calls
- Use `pytest-mock` for patching. Never use `unittest.mock` directly in test files
- Never test against live services in CI. Stub at the interface boundary
- Assert on the exact shape of returned data — not just "it didn't crash"

### conftest.py (root level)

```python
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
```

This ensures `from src.services.db_service import DBService` works from any test file without install.

---

## 7. Python Coding Standards

### Type annotations — always modern syntax

```python
# Wrong
from typing import List, Dict, Optional, Tuple
def foo(x: List[str]) -> Optional[Dict[str, int]]: ...

# Correct (Python 3.10+)
def foo(x: list[str]) -> dict[str, int] | None: ...

# Return tuples
def bar() -> tuple[str, bool]: ...   # not -> (str, bool) — that's not valid
```

### Imports — always at module top-level

```python
# Wrong — PLC0415
def my_method(self):
    import uuid
    return str(uuid.uuid4())

# Correct
import uuid

def my_method(self):
    return str(uuid.uuid4())
```

### isinstance — always use union syntax

```python
# Wrong — UP038
if isinstance(value, (int, float)):

# Correct
if isinstance(value, int | float):
```

### Datetime — use datetime.UTC

```python
# Wrong
from datetime import timezone
datetime.now(timezone.utc)

# Correct (Python 3.11+)
from datetime import datetime
datetime.now(datetime.UTC)
```

### Security — SQL injection prevention

When building queries with user-supplied table or column names, quote identifiers:

```python
# Dangerous — table_name injected directly
cursor.execute(f"SELECT * FROM {table_name}")

# Safe — double-quote and escape
safe_table = table_name.replace('"', '""')
cursor.execute(f'SELECT * FROM "{safe_table}"')
```

Parameterize all values. Only identifiers (table/column names) need manual quoting since SQLite's `?` placeholder doesn't support them.

### Logging — not print

```python
import logging
logger = logging.getLogger(__name__)

# Use structured levels
logger.info("Processing %d emails", count)
logger.warning("Duplicate skipped: %s", message_id)
logger.error("Classification failed", exc_info=True)
```

Never use `print()` in service or provider code. `print()` is acceptable only in `scripts/`.

### Exception handling — no silent swallowing

```python
# Wrong
try:
    result = risky_call()
except Exception:
    pass

# Correct — log it, re-raise if caller needs to know, or return a safe default
try:
    result = risky_call()
except ValueError as e:
    logger.warning("Skipping record: %s", e)
    return None
```

---

## 8. Data Model Decisions

### Deduplication

Use a deterministic hash as the primary natural key for any ingested record:

```python
import hashlib

def make_message_id(sender: str, subject: str, content: str) -> str:
    raw = f"{sender}|{subject}|{content[:200]}"
    return hashlib.sha256(raw.encode()).hexdigest()
```

Use `INSERT OR IGNORE` in SQLite for idempotent batch re-runs.

### SQLite production settings

Always set these on connection init:

```python
conn.execute("PRAGMA journal_mode=WAL")   # concurrent reads while writing
conn.execute("PRAGMA foreign_keys=ON")    # enforce referential integrity
conn.row_factory = sqlite3.Row            # access columns by name, not index
```

### Storing lists in SQLite

SQLite has no array type. Use `json.dumps` / `json.loads`:

```python
# Save
key_indicators_json = json.dumps(result.key_indicators)

# Load
key_indicators = json.loads(row["key_indicators"] or "[]")
```

---

## 9. README Consistency Rules

The README is a contract with the user. Keep it in sync with the code on every release:

| README section | Must match |
|---|---|
| Version badge | `VERSION` file |
| Python version | `pyproject.toml` `target-version` and actual minimum tested |
| Categories / features | Exact strings used in code (prompts, dropdowns, DB values) |
| Test count | Actual `pytest tests/ --collect-only` count |
| Project structure tree | Actual directory layout |
| Data flow diagram | Actual pipeline order in `app.py` |

A stale README is a bug. Update it in the same commit as the feature or fix that changed the behavior.

---

## 10. What Not To Do

- **Do not add Co-Authored-By or AI attribution** to any commit, PR, comment, or file. All output is the author's work.
- **Do not commit directly to `main` or `dev`**. Every change goes through a branch + PR.
- **Do not add speculative features**. If the task doesn't require it, don't build it.
- **Do not add error handling for impossible scenarios**. Trust your own interfaces.
- **Do not write docstrings for code you didn't change**.
- **Do not use backwards-compatibility shims** when you can just update the code.
- **Do not leave categories, feature flags, or data values half-removed**. If something is removed, remove it everywhere: prompts, dropdowns, tests, README, changelog.
- **Do not use `typing.List`, `typing.Dict`, `typing.Optional`** in new code. Use built-in generics.
- **Do not store original (unmasked) PII in the audit log**. Store only the masked version.
