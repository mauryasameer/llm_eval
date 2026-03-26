"""
conftest.py
-----------
Pytest configuration for the llm-eval-framework test suite.
Ensures deepeval's pytest plugin (which is incompatible with Python 3.9) 
does not block our own test collection.
"""
collect_ignore_glob = []

# Suppress deepeval's auto-registered pytest plugin to avoid Python 3.9
# incompatibility with PEP 604 union syntax (X | Y).
def pytest_configure(config):
    import sys
    if sys.version_info < (3, 10):
        config.pluginmanager.set_blocked("deepeval")
