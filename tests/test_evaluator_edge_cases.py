"""
Edge-case tests for the Evaluator module.

Tests robustness with unusual inputs: empty strings, very long responses,
unicode, special characters, single-word answers, and boundary conditions.
"""

import pytest

from holodeck.evaluator import EvalResult, Evaluator, _sentences


class TestEvaluatorEdgeCases:
    """Test evaluator with unusual and boundary inputs."""

    def setup_method(self):
        self.evaluator = Evaluator()

    # ─── Empty / Degenerate Inputs ───────────────────────────

    def test_empty_response(self):
        """Empty string should not crash and should score very low."""
        result = self.evaluator.evaluate(
            response="",
            expected_keywords=["thermostat", "coolant"],
            scenario={"difficulty": "easy"},
            task_type="engine_diagnosis",
        )
        assert result.composite < 0.2
        assert not result.passed
        assert len(result.matched_keywords) == 0
        assert len(result.missed_keywords) == 2

    def test_single_word_response(self):
        """Single word should score low on completeness."""
        result = self.evaluator.evaluate(
            response="thermostat",
            expected_keywords=["thermostat", "coolant", "overheating"],
            scenario={"difficulty": "easy"},
            task_type="engine_diagnosis",
        )
        assert result.accuracy > 0  # Found 1/3 keywords
        assert result.completeness < 0.4

    def test_whitespace_only_response(self):
        """Whitespace-only should not crash."""
        result = self.evaluator.evaluate(
            response="   \n\t  \n  ",
            expected_keywords=["fire"],
            scenario={"difficulty": "easy"},
            task_type="emergency_response",
        )
        assert not result.passed

    def test_no_keywords_provided(self):
        """Empty keyword list should not crash."""
        result = self.evaluator.evaluate(
            response="The engine is fine.",
            expected_keywords=[],
            scenario={"difficulty": "easy"},
            task_type="engine_diagnosis",
        )
        # accuracy divides by max(1, len(expected)) so should be 0/1 = 0
        assert result.accuracy == 0.0

    # ─── Very Long Inputs ────────────────────────────────────

    def test_very_long_response(self):
        """Very long response should be scored without crashing."""
        long_text = "thermostat coolant overheating. " * 500
        result = self.evaluator.evaluate(
            response=long_text,
            expected_keywords=["thermostat", "coolant", "overheating"],
            scenario={"difficulty": "easy"},
            task_type="engine_diagnosis",
        )
        assert result.accuracy == 1.0
        assert result.passed

    def test_long_repetitive_response(self):
        """Long but repetitive text — tests specificity scoring."""
        text = "check the thing. " * 200
        result = self.evaluator.evaluate(
            response=text,
            expected_keywords=["check"],
            scenario={"difficulty": "easy"},
            task_type="engine_diagnosis",
        )
        assert result.accuracy == 1.0  # Found the keyword

    # ─── Unicode and Special Characters ──────────────────────

    def test_unicode_response(self):
        """Unicode characters should not break the evaluator."""
        result = self.evaluator.evaluate(
            response="The thermostat is broken — it's stuck closed! "
            "Coolant temperature is 220°F. Overheating imminent. "
            "Régler le problème: replace thermostat. 🚢",
            expected_keywords=["thermostat", "coolant", "overheating"],
            scenario={"difficulty": "easy"},
            task_type="engine_diagnosis",
        )
        assert result.accuracy == 1.0

    def test_html_tags_in_response(self):
        """HTML-like tags should be treated as text."""
        result = self.evaluator.evaluate(
            response="<p>thermostat is broken</p>",
            expected_keywords=["thermostat"],
            scenario={"difficulty": "easy"},
            task_type="engine_diagnosis",
        )
        assert result.accuracy == 1.0

    def test_newlines_and_tabs(self):
        """Response with lots of whitespace characters."""
        result = self.evaluator.evaluate(
            response="Step 1:\n\tCheck thermostat\nStep 2:\n\tCheck coolant\nStep 3:\n\tCheck for overheating",
            expected_keywords=["thermostat", "coolant", "overheating"],
            scenario={"difficulty": "easy"},
            task_type="engine_diagnosis",
        )
        assert result.accuracy == 1.0

    # ─── Boundary Scores ─────────────────────────────────────

    def test_perfect_keyword_match(self):
        """All keywords present = accuracy 1.0."""
        result = self.evaluator.evaluate(
            response="thermostat coolant overheating impeller bearing",
            expected_keywords=["thermostat", "coolant", "overheating", "impeller", "bearing"],
            scenario={"difficulty": "easy"},
            task_type="engine_diagnosis",
        )
        assert result.accuracy == 1.0

    def test_zero_keyword_match(self):
        """No keywords present = accuracy 0.0."""
        result = self.evaluator.evaluate(
            response="I think the boat needs more paint and maybe some new curtains.",
            expected_keywords=["thermostat", "coolant", "overheating"],
            scenario={"difficulty": "easy"},
            task_type="engine_diagnosis",
        )
        assert result.accuracy == 0.0

    def test_case_insensitive_keywords(self):
        """Keywords should match regardless of case."""
        result = self.evaluator.evaluate(
            response="THERMOSTAT Coolant OVERHEATING",
            expected_keywords=["thermostat", "coolant", "overheating"],
            scenario={"difficulty": "easy"},
            task_type="engine_diagnosis",
        )
        assert result.accuracy == 1.0

    # ─── Pass Threshold Boundaries ───────────────────────────

    def test_custom_threshold_zero(self):
        """Threshold of 0.0 means everything passes."""
        evaluator = Evaluator(pass_threshold=0.0)
        result = evaluator.evaluate(
            response="I don't know anything.",
            expected_keywords=["thermostat"],
            scenario={"difficulty": "easy"},
            task_type="engine_diagnosis",
        )
        assert result.passed

    def test_custom_threshold_one(self):
        """Threshold of 1.0 means almost nothing passes."""
        evaluator = Evaluator(pass_threshold=1.0)
        result = evaluator.evaluate(
            response="thermostat coolant overheating",
            expected_keywords=["thermostat", "coolant", "overheating"],
            scenario={"difficulty": "easy"},
            task_type="engine_diagnosis",
        )
        # composite won't reach 1.0 unless every dimension is perfect
        assert not result.passed

    # ─── Helper Function Tests ───────────────────────────────

    def test_sentences_split(self):
        """_sentences should split on .!? properly."""
        result = _sentences("Hello. World! How are you? Fine.")
        assert len(result) == 4

    def test_sentences_empty(self):
        """_sentences on empty string returns empty list."""
        assert _sentences("") == []

    def test_sentences_no_punctuation(self):
        """_sentences on text without punctuation returns one item."""
        result = _sentences("no punctuation here")
        assert len(result) == 1

    # ─── EvalResult Dataclass ────────────────────────────────

    def test_eval_result_to_dict(self):
        """EvalResult.to_dict should produce a proper dict."""
        er = EvalResult(
            accuracy=0.8,
            specificity=0.6,
            reasoning=0.7,
            completeness=0.5,
            composite=0.65,
            passed=True,
            matched_keywords=["a", "b"],
            missed_keywords=["c"],
        )
        d = er.to_dict()
        assert d["accuracy"] == 0.8
        assert d["passed"] is True
        assert d["matched_keywords"] == ["a", "b"]
        assert d["missed_keywords"] == ["c"]
        assert "details" in d

    def test_eval_result_default_details(self):
        """EvalResult should have empty dict as default details."""
        er = EvalResult(
            accuracy=0.5, specificity=0.5, reasoning=0.5,
            completeness=0.5, composite=0.5, passed=False,
        )
        assert er.details == {}
        assert er.matched_keywords == []
        assert er.missed_keywords == []

    # ─── Specificity Scoring Details ─────────────────────────

    def test_specificity_with_numbers(self):
        """Numbers in response boost specificity."""
        result_with_numbers = self.evaluator.evaluate(
            response="The temperature is 220°F and pressure is 15 PSI. "
            "Check the thermostat. Replace the coolant.",
            expected_keywords=["thermostat", "coolant"],
            scenario={"difficulty": "easy"},
            task_type="engine_diagnosis",
        )
        result_without = self.evaluator.evaluate(
            response="The temperature is high and pressure is low. "
            "Check the thermostat. Replace the coolant.",
            expected_keywords=["thermostat", "coolant"],
            scenario={"difficulty": "easy"},
            task_type="engine_diagnosis",
        )
        assert result_with_numbers.specificity >= result_without.specificity

    def test_reasoning_with_connectors(self):
        """Causal connectors boost reasoning score."""
        result_with = self.evaluator.evaluate(
            response="Because the thermostat is stuck, coolant cannot circulate. "
            "Therefore, the engine overheats. First, check the thermostat. "
            "Then, inspect the coolant level.",
            expected_keywords=["thermostat", "coolant"],
            scenario={"difficulty": "easy"},
            task_type="engine_diagnosis",
        )
        result_without = self.evaluator.evaluate(
            response="The thermostat is broken. The coolant is low. "
            "The engine is hot.",
            expected_keywords=["thermostat", "coolant"],
            scenario={"difficulty": "easy"},
            task_type="engine_diagnosis",
        )
        assert result_with.reasoning >= result_without.reasoning
