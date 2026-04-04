"""
tests/unit/test_accuracy.py
---------------------------
Unit tests for the FinancialNormalizer and evaluate_financial_f1 evaluator.
"""
import pytest

from src.services.accuracy_service import FinancialNormalizer, evaluate_financial_f1


class TestFinancialNormalizer:
    """Tests for numerical string normalisation."""

    @pytest.mark.parametrize("raw, expected", [
        ("10 billion",           10_000_000_000.0),
        ("$10.5B",               10_500_000_000.0),
        ("£500m",                500_000_000.0),
        ("€1.2k",                1_200.0),
        ("1.000.000,00",         1_000_000.0),   # EU format
        ("1,000,000.00",         1_000_000.0),   # US format
        ("1.5 million",          1_500_000.0),
        ("500k",                 500_000.0),
        ("2.5T",                 2_500_000_000_000.0),
        ("$10,000,000,000",      10_000_000_000.0),
    ])
    def test_scale_normalisation(self, raw, expected):
        result = FinancialNormalizer.normalize_amount(raw)
        assert result == pytest.approx(expected), f"'{raw}' -> expected {expected}, got {result}"

    def test_invalid_input_returns_original(self):
        result = FinancialNormalizer.normalize_amount("not-a-number")
        assert result == "not-a-number"


class TestFinancialF1:
    """Tests for the weighted F1 evaluator."""

    def test_perfect_match_gives_high_f1(self):
        gold = "Apple ($AAPL) earned $10 Billion in Q3 2024."
        pred = "Apple (AAPL) made $10,000,000,000 in Q3 2024."
        result = evaluate_financial_f1(gold, pred)
        assert result["f1_score"] > 0.85, "Normalised equivalent amounts should yield high F1."

    def test_wrong_amount_lowers_f1(self):
        gold = "Revenue was $10B in Q3 2024."
        pred = "Revenue was $5B in Q3 2024."
        result = evaluate_financial_f1(gold, pred)
        assert result["f1_score"] < 1.0, "Mismatched amounts should not yield perfect F1."

    def test_result_keys_present(self):
        result = evaluate_financial_f1("AAPL rose 5%.", "AAPL fell 5%.")
        for key in ("metric", "precision", "recall", "f1_score", "details"):
            assert key in result, f"Missing key: {key}"

    def test_scores_bounded(self):
        result = evaluate_financial_f1("TSLA $200", "TSLA $200")
        assert 0.0 <= result["precision"] <= 1.0
        assert 0.0 <= result["recall"] <= 1.0
        assert 0.0 <= result["f1_score"] <= 1.0
