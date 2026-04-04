"""
conftest.py
-----------
Pytest configuration for the llm-eval-framework test suite.

Inserts the repo root into sys.path so that `from src.services.*` imports
work from any test file without installing the package.

Also suppresses deepeval's pytest plugin which registers hooks incompatible
with the standard pytest suite.
"""
import os
import sys

# Ensure `from src.*` imports resolve correctly in all test files
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

collect_ignore_glob = []


def pytest_configure(config):
    config.pluginmanager.set_blocked("deepeval")
