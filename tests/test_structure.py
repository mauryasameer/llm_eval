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
import json
import os
import re
import sys

import pytest
import yaml

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


# ── README project structure matches actual repo ──────────────────────────────

def _parse_readme_tree() -> list[str]:
    """
    Extract every path mentioned in the '📂 Project Structure' code block
    in README.md and return them as relative POSIX paths.
    """
    readme = repo_path("README.md")
    with open(readme, encoding="utf-8") as f:
        content = f.read()

    # Grab the fenced code block that follows the Project Structure heading
    match = re.search(
        r"##\s+.*?Project Structure.*?```(?:text)?\n(.*?)```",
        content,
        re.DOTALL | re.IGNORECASE,
    )
    assert match, "Could not find '📂 Project Structure' code block in README.md"
    tree = match.group(1)

    paths = []
    stack: list[str] = []

    for raw_line in tree.splitlines():
        # Strip inline comments
        line = raw_line.split("#")[0].rstrip()
        # Find the branch marker
        branch = re.search(r"[├└]──\s+", line)
        if not branch:
            continue

        prefix = line[: branch.start()]
        name = line[branch.end():].strip().rstrip("/")
        if not name:
            continue

        # Depth = number of 4-char groups before the branch marker
        depth = len(prefix) // 4
        stack = stack[:depth]
        stack.append(name)

        # Skip the repo root label (first token without a parent)
        if len(stack) > 0:
            paths.append("/".join(stack))

    return paths


def test_readme_structure_paths_exist():
    """
    Every file/directory listed in the README '📂 Project Structure' section
    must actually exist in the repo. This test would have caught the stale
    core/models/local_model.py and core/report_engine/generator.py entries.
    """
    missing = []
    for rel in _parse_readme_tree():
        full = repo_path(rel)
        if not os.path.exists(full):
            missing.append(rel)

    assert not missing, (
        f"README lists {len(missing)} path(s) that don't exist in the repo:\n"
        + "\n".join(f"  ✗ {p}" for p in missing)
    )


# ── HuggingFace Space required files ─────────────────────────────────────────

HF_SPACE_REQUIRED = [
    "hf_space/app.py",
    "hf_space/requirements.txt",
]


@pytest.mark.parametrize("rel_path", HF_SPACE_REQUIRED)
def test_hf_space_file_exists(rel_path):
    assert os.path.isfile(repo_path(rel_path)), f"HF Space file missing: {rel_path}"


def test_hf_space_requirements_has_core_packages():
    """hf_space/requirements.txt must declare gradio and transformers."""
    path = repo_path("hf_space/requirements.txt")
    with open(path) as f:
        contents = f.read().lower()
    for pkg in ("gradio", "transformers", "jinja2"):
        assert pkg in contents, f"hf_space/requirements.txt is missing '{pkg}'"


def test_hf_space_app_has_launch_call():
    path = repo_path("hf_space/app.py")
    with open(path) as f:
        source = f.read()
    assert "demo.launch(" in source, "hf_space/app.py must call demo.launch()"


def test_hf_space_app_ssr_disabled():
    """SSR mode must be off — it caused startup hangs in Gradio 6."""
    path = repo_path("hf_space/app.py")
    with open(path) as f:
        source = f.read()
    assert "ssr_mode=False" in source, (
        "hf_space/app.py must set ssr_mode=False in demo.launch() to prevent Gradio 6 startup hangs"
    )


# ── Accuracy test data schema ─────────────────────────────────────────────────

def test_accuracy_tests_file_exists():
    assert os.path.isfile(repo_path("data/gold_standard/accuracy_tests.json"))


def test_accuracy_tests_schema():
    path = repo_path("data/gold_standard/accuracy_tests.json")
    with open(path) as f:
        data = json.load(f)
    assert isinstance(data, list), "accuracy_tests.json must be a JSON array"
    assert len(data) >= 1, "accuracy_tests.json must have at least one test case"
    for i, entry in enumerate(data):
        for key in ("name", "prompt", "gold"):
            assert key in entry, f"accuracy_tests.json entry {i} is missing key '{key}'"


# ── Regulatory mapping YAML completeness ─────────────────────────────────────

def test_regulatory_mapping_yaml_schema():
    path = repo_path("configs/regulatory_mapping.yaml")
    with open(path) as f:
        config = yaml.safe_load(f)
    assert "mapping" in config, "regulatory_mapping.yaml must have a top-level 'mapping' key"
    for entry in config["mapping"]:
        for key in ("metric", "control", "intent"):
            assert key in entry, f"regulatory_mapping.yaml entry missing key '{key}': {entry}"


REQUIRED_METRICS = {"financial_f1", "injection_pass_rate", "explainability_score"}


def test_regulatory_mapping_has_required_metrics():
    path = repo_path("configs/regulatory_mapping.yaml")
    with open(path) as f:
        config = yaml.safe_load(f)
    mapped = {e["metric"] for e in config["mapping"]}
    missing = REQUIRED_METRICS - mapped
    assert not missing, f"regulatory_mapping.yaml is missing metrics: {missing}"


# ── CI workflow integrity ─────────────────────────────────────────────────────

def test_ci_workflow_runs_pytest():
    path = repo_path(".github/workflows/ci.yml")
    with open(path) as f:
        content = f.read()
    assert "pytest" in content, "ci.yml must invoke pytest"


def test_deploy_workflow_targets_main_only():
    path = repo_path(".github/workflows/deploy_hf_space.yml")
    with open(path) as f:
        content = f.read()
    assert "branches: [main]" in content or "branches:\n      - main" in content, (
        "deploy_hf_space.yml must only deploy from the main branch"
    )


def test_ci_workflow_references_push_script():
    """The CI workflow (not the standalone deploy workflow) invokes push_to_hf.sh."""
    path = repo_path(".github/workflows/ci.yml")
    with open(path) as f:
        content = f.read()
    assert "push_to_hf.sh" in content, "ci.yml must reference scripts/push_to_hf.sh for HF deployment"
