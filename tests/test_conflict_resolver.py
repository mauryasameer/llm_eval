"""
tests/test_conflict_resolver.py
--------------------------------
Unit tests for the ConflictResolver RTM engine.
"""
from core.utils.mapper import RegulatoryMapper
from core.reporting.conflict_resolver import ConflictResolver


class TestConflictResolver:

    def setup_method(self):
        self.mapper = RegulatoryMapper()
        self.resolver = ConflictResolver(self.mapper)

    def test_no_conflict_when_both_pass(self):
        trail = [
            {"regulatory_control": "EU AI Act Article 15 (Transparency)", "score": "PASS"},
            {"regulatory_control": "GDPR (Data Minimization)", "score": "PASS"},
        ]
        conflicts = self.resolver.resolve(trail)
        assert len(conflicts) == 0

    def test_no_conflict_when_both_fail(self):
        trail = [
            {"regulatory_control": "EU AI Act Article 15 (Transparency)", "score": "FAIL"},
            {"regulatory_control": "GDPR (Data Minimization)", "score": "FAIL"},
        ]
        conflicts = self.resolver.resolve(trail)
        assert len(conflicts) == 0

    def test_conflict_detected_when_pass_meets_failed_counterpart(self):
        trail = [
            {"regulatory_control": "EU AI Act Article 15 (Transparency)", "score": "PASS"},
            {"regulatory_control": "GDPR (Data Minimization)", "score": "FAIL"},
        ]
        conflicts = self.resolver.resolve(trail)
        assert len(conflicts) == 1
        assert "EU AI Act Article 15 (Transparency)" in conflicts[0]["passed_control"]
        assert "GDPR (Data Minimization)" in conflicts[0]["failed_control"]

    def test_conflict_is_not_duplicated(self):
        """Bidirectional mapping should not produce two conflict entries."""
        trail = [
            {"regulatory_control": "EU AI Act Article 15 (Transparency)", "score": "PASS"},
            {"regulatory_control": "GDPR (Data Minimization)", "score": "FAIL"},
        ]
        conflicts = self.resolver.resolve(trail)
        assert len(conflicts) == 1, "Bidirectional conflict should be reported only once."

    def test_conflict_entry_has_required_keys(self):
        trail = [
            {"regulatory_control": "EU AI Act Article 15 (Transparency)", "score": "PASS"},
            {"regulatory_control": "GDPR (Data Minimization)", "score": "FAIL"},
        ]
        conflict = self.resolver.resolve(trail)[0]
        for key in ("passed_control", "failed_control", "reason"):
            assert key in conflict, f"Missing key in conflict output: {key}"
