"""
tests/test_structure.py
------------------------
Structural sanity tests — catches missing files, broken imports, and invalid
CLI entry points BEFORE they reach production. These tests are deliberately
simple but comprehensive: they are the "lint layer" that would have caught
the missing main.py before the user noticed it.
"""
import ast
import importlib
import os
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def repo_path(*parts) -> str:
    return os.path.join(REPO_ROOT, *parts)


# ── Required files exist ──────────────────────────────────────────────────────

REQUIRED_FILES = [
    "main.py",
    "requirements.txt",
    "README.md",
    ".gitignore",
    "pytest.ini",
    "conftest.py",
    "configs/regulatory_mapping.yaml",
    "configs/system_prompts.yaml",
    "data/adversarial_library/jailbreaks.json",
    "reports/templates/report_template.html",
    "core/__init__.py",
    "core/evaluators/__init__.py",
    "core/evaluators/accuracy.py",
    "core/evaluators/adversarial.py",
    "core/evaluators/explainability.py",
    "core/evaluators/report_generator.py",
    "core/utils/__init__.py",
    "core/utils/mapper.py",
    "core/reporting/__init__.py",
    "core/reporting/conflict_resolver.py",
    "scripts/download_model.py",
    ".github/workflows/ci.yml",
]


@pytest.mark.parametrize("rel_path", REQUIRED_FILES)
def test_required_file_exists(rel_path):
    """Fail loudly if a critical project file is missing."""
    full = repo_path(rel_path)
    assert os.path.isfile(full), f"Required file is missing: {rel_path}"


# ── Python files are valid syntax ─────────────────────────────────────────────

PYTHON_MODULES = [
    "main.py",
    "core/evaluators/accuracy.py",
    "core/evaluators/adversarial.py",
    "core/evaluators/explainability.py",
    "core/evaluators/report_generator.py",
    "core/utils/mapper.py",
    "core/reporting/conflict_resolver.py",
    "scripts/download_model.py",
    "scripts/generate_jailbreaks.py",
]


@pytest.mark.parametrize("rel_path", PYTHON_MODULES)
def test_python_file_is_valid_syntax(rel_path):
    """Parse each critical Python file to catch syntax errors instantly."""
    full = repo_path(rel_path)
    with open(full, "r", encoding="utf-8") as f:
        source = f.read()
    try:
        ast.parse(source)
    except SyntaxError as exc:
        pytest.fail(f"Syntax error in {rel_path}: {exc}")


# ── Core modules are importable ───────────────────────────────────────────────

@pytest.mark.parametrize("module", [
    "core.evaluators.accuracy",
    "core.evaluators.adversarial",
    "core.utils.mapper",
    "core.reporting.conflict_resolver",
])
def test_module_importable(module):
    """Ensure core modules can be imported without crashing."""
    sys.path.insert(0, REPO_ROOT)
    try:
        importlib.import_module(module)
    except ImportError as exc:
        # Only fail on our own code — not optional ML deps like mlx/torch
        if "mlx" not in str(exc) and "torch" not in str(exc) and "transformers" not in str(exc):
            pytest.fail(f"Cannot import {module}: {exc}")


# ── main.py has the expected CLI arguments ────────────────────────────────────

def test_main_has_model_arg():
    full = repo_path("main.py")
    with open(full) as f:
        source = f.read()
    assert "--model" in source, "main.py must define a --model CLI argument"


def test_main_has_eval_arg():
    full = repo_path("main.py")
    with open(full) as f:
        source = f.read()
    assert "--eval" in source, "main.py must define an --eval CLI argument"


def test_main_has_report_arg():
    full = repo_path("main.py")
    with open(full) as f:
        source = f.read()
    assert "--report" in source, "main.py must define a --report CLI argument"


# ── Adversarial library is valid JSON with correct schema ────────────────────

def test_adversarial_library_is_valid_json():
    import json
    path = repo_path("data/adversarial_library/jailbreaks.json")
    with open(path) as f:
        data = json.load(f)
    assert isinstance(data, list), "jailbreaks.json must be a JSON array"
    assert len(data) >= 10, f"Expected at least 10 jailbreak entries, got {len(data)}"


REQUIRED_JAILBREAK_KEYS = {"id", "category", "attack_vector", "prompt", "expected_safe_behavior"}


def test_adversarial_library_schema():
    import json
    path = repo_path("data/adversarial_library/jailbreaks.json")
    with open(path) as f:
        data = json.load(f)
    for i, entry in enumerate(data):
        missing = REQUIRED_JAILBREAK_KEYS - set(entry.keys())
        assert not missing, f"Entry {i} (id={entry.get('id')}) is missing keys: {missing}"


# ── Report generator handles partial metrics without crashing ─────────────────

def test_report_generator_partial_metrics():
    """Regression: ensure report generation doesn't crash when only one eval module ran."""
    sys.path.insert(0, REPO_ROOT)
    from core.evaluators.report_generator import generate_html_report

    # Only adversarial ran — accuracy and explainability are absent
    partial_metrics = {"safety": 0.8}
    audit_trail = [{
        "test_name": "Test",
        "category": "Safety / Adversarial",
        "response": "I cannot fulfill this request.",
        "score": "PASS",
        "regulatory_control": "SR 11-7 Section 3.1",
        "regulatory_intent": "Robustness",
    }]

    # report_generator resolves paths relative to repo root — use a known location
    output_rel = "reports/test_partial_metrics_report.html"
    output_abs = repo_path(output_rel)

    # Must not raise UndefinedError or any other exception
    generate_html_report(partial_metrics, audit_trail, output_filename=output_rel)

    assert os.path.isfile(output_abs), "Report file was not created"
    with open(output_abs) as f:
        content = f.read()
    assert "<html" in content.lower(), "Output does not look like valid HTML"

    # Cleanup
    os.remove(output_abs)

