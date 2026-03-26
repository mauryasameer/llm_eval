"""
tests/test_mapper.py
--------------------
Unit tests for the RegulatoryMapper config loader.
"""
from core.utils.mapper import RegulatoryMapper


class TestRegulatoryMapper:

    def setup_method(self):
        self.mapper = RegulatoryMapper()

    def test_known_metric_returns_control(self):
        result = self.mapper.get_mapping("financial_f1")
        assert result["control"] == "SR 11-7 Section 3.2"

    def test_known_metric_returns_intent(self):
        result = self.mapper.get_mapping("injection_pass_rate")
        assert "robustness" in result["intent"].lower() or result["intent"]

    def test_unknown_metric_returns_fallback(self):
        result = self.mapper.get_mapping("nonexistent_metric")
        assert result["control"] == "Unknown"
        assert "No regulatory mapping found" in result["intent"]

    def test_conflicts_with_field_present(self):
        result = self.mapper.get_mapping("transparency_score")
        assert "conflicts_with" in result, "transparency_score should have a conflicts_with field."

    def test_all_entries_have_required_keys(self):
        for metric, data in self.mapper.mapping.items():
            assert "control" in data, f"Missing 'control' in metric: {metric}"
            assert "intent" in data, f"Missing 'intent' in metric: {metric}"
