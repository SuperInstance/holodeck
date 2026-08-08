"""
Tests for evaluator _score_completeness with max_points parameter.

BUG-2: max_points was accepted but never used in the scoring logic.
After the fix, max_points contributes to a keyword-coverage sub-score
that's blended with the length/structure score.
"""

import pytest
from holodeck.evaluator import Evaluator, EvalResult


@pytest.fixture
def evaluator():
    return Evaluator()


@pytest.fixture
def scenario():
    return {
        "prompt": "Diagnose the problem...",
        "difficulty": "medium",
        "expected_keywords": ["thermostat", "coolant", "circulation", "replace", "hose"],
    }


class TestMaxPointsScoring:
    """Verify that max_points is actually used in _score_completeness."""

    def test_max_points_affects_completeness_score(self, evaluator, scenario):
        """Same response scored with different max_points should differ."""
        response = (
            "The thermostat is stuck closed, preventing coolant circulation. "
            "Because the upper hose is hot but the lower is cool, this confirms "
            "no flow through the system. Therefore, I recommend replacing the "
            "thermostat immediately.\n\n"
            "1. Shut down engine\n"
            "2. Remove housing\n"
            "3. Replace thermostat\n"
            "4. Refill coolant\n"
            "5. Verify repair"
        )
        # With max_points = 5 (matches 5 keywords), coverage is high
        result_default = evaluator.evaluate(
            response=response,
            expected_keywords=["thermostat", "coolant", "circulation", "replace", "hose"],
            scenario=scenario,
            task_type="engine_diagnosis",
        )

        # With max_points = 1, the coverage component is always high
        result_one = evaluator.evaluate(
            response=response,
            expected_keywords=["thermostat", "coolant", "circulation", "replace", "hose"],
            scenario=scenario,
            task_type="engine_diagnosis",
            max_points=1,
        )

        # With max_points = 100, the coverage component will be very low
        result_hundred = evaluator.evaluate(
            response=response,
            expected_keywords=["thermostat", "coolant", "circulation", "replace", "hose"],
            scenario=scenario,
            task_type="engine_diagnosis",
            max_points=100,
        )

        # max_points=1 should give higher completeness than max_points=100
        # because with only 1 expected point, finding 5/1 keywords is 100% coverage
        assert result_one.completeness >= result_hundred.completeness

    def test_max_points_zero_is_safe(self, evaluator, scenario):
        """max_points=0 should not crash (division by zero protection)."""
        result = evaluator.evaluate(
            response="thermostat coolant circulation",
            expected_keywords=["thermostat", "coolant", "circulation"],
            scenario=scenario,
            task_type="engine_diagnosis",
            max_points=0,
        )
        assert isinstance(result.completeness, float)
        assert 0.0 <= result.completeness <= 1.0

    def test_max_points_none_falls_back_to_keyword_count(self, evaluator, scenario):
        """max_points=None should default to len(expected_keywords)."""
        response = (
            "The thermostat is stuck closed. Coolant is not circulating. "
            "Replace the thermostat. Check the hose for damage."
        )
        result_default = evaluator.evaluate(
            response=response,
            expected_keywords=["thermostat", "coolant", "circulation", "replace", "hose"],
            scenario=scenario,
            task_type="engine_diagnosis",
        )
        # This is equivalent to max_points = len(expected_keywords) = 5
        result_explicit = evaluator.evaluate(
            response=response,
            expected_keywords=["thermostat", "coolant", "circulation", "replace", "hose"],
            scenario=scenario,
            task_type="engine_diagnosis",
            max_points=5,
        )
        assert abs(result_default.completeness - result_explicit.completeness) < 0.01

    def test_high_max_points_penalizes_sparse_response(self, evaluator, scenario):
        """A response covering few of many expected points should score lower."""
        # Need >50 words to get past the early-return thresholds
        sparse_response = (
            "I think the problem is the thermostat. You should check it and "
            "replace it if needed. Make sure to follow proper procedure when "
            "doing this repair. The coolant system is important for engine "
            "health and proper operation. Always verify your work after "
            "completing the repair to ensure everything functions correctly."
        )
        # Many expected points → finding only a few is less complete
        result_many_points = evaluator.evaluate(
            response=sparse_response,
            expected_keywords=["thermostat", "coolant", "circulation", "replace", "hose"],
            scenario=scenario,
            task_type="engine_diagnosis",
            max_points=50,
        )
        # Few expected points → finding the same few is more complete
        result_few_points = evaluator.evaluate(
            response=sparse_response,
            expected_keywords=["thermostat", "coolant", "circulation", "replace", "hose"],
            scenario=scenario,
            task_type="engine_diagnosis",
            max_points=3,
        )
        assert result_few_points.completeness > result_many_points.completeness
