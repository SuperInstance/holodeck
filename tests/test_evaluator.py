"""Tests for the holodeck evaluator."""

import pytest
from holodeck.evaluator import Evaluator, EvalResult


@pytest.fixture
def evaluator():
    return Evaluator()


@pytest.fixture
def good_response():
    return (
        "Based on the symptoms, the thermostat is stuck closed. "
        "The key indicator is the temperature differential between the upper "
        "and lower hoses — the upper hose is hot at 220°F while the lower "
        "hose is cool, indicating no coolant circulation. "
        "Because the coolant level is normal and the raw water intake is clear, "
        "we can rule out low coolant or blockage. Therefore, the thermostat must "
        "be the culprit. I recommend replacing the thermostat and checking "
        "for any damage from overheating.\n\n"
        "Steps:\n"
        "1. Shut down the engine and let it cool\n"
        "2. Remove the thermostat housing\n"
        "3. Inspect the old thermostat for visible sticking\n"
        "4. Install a new thermostat with a new gasket\n"
        "5. Refill coolant and bleed air from the system\n"
        "6. Verify temperature returns to normal operating range"
    )


@pytest.fixture
def poor_response():
    return "The engine is too hot. Check the water maybe."


@pytest.fixture
def scenario():
    return {
        "prompt": "Diagnose the engine problem...",
        "difficulty": "easy",
    }


EXPECTED_KEYWORDS = [
    "thermostat", "stuck closed", "coolant", "circulation",
    "replace", "overheating",
]


class TestEvaluator:
    def test_good_response_scores_high(self, evaluator, good_response, scenario):
        result = evaluator.evaluate(
            response=good_response,
            expected_keywords=EXPECTED_KEYWORDS,
            scenario=scenario,
            task_type="engine_diagnosis",
        )
        assert result.accuracy > 0.5
        assert result.composite > 0.3
        assert result.passed

    def test_poor_response_scores_low(self, evaluator, poor_response, scenario):
        result = evaluator.evaluate(
            response=poor_response,
            expected_keywords=EXPECTED_KEYWORDS,
            scenario=scenario,
            task_type="engine_diagnosis",
        )
        assert result.accuracy < 0.5
        assert not result.passed

    def test_keyword_matching(self, evaluator, good_response, scenario):
        result = evaluator.evaluate(
            response=good_response,
            expected_keywords=EXPECTED_KEYWORDS,
            scenario=scenario,
            task_type="engine_diagnosis",
        )
        # Should match several keywords
        assert len(result.matched_keywords) >= 3
        assert "thermostat" in result.matched_keywords
        assert "coolant" in result.matched_keywords

    def test_missed_keywords_tracked(self, evaluator, poor_response, scenario):
        result = evaluator.evaluate(
            response=poor_response,
            expected_keywords=EXPECTED_KEYWORDS,
            scenario=scenario,
            task_type="engine_diagnosis",
        )
        assert len(result.missed_keywords) >= 3
        assert "thermostat" in result.missed_keywords

    def test_specificity_increases_with_detail(self, evaluator, scenario):
        vague = "Something is wrong with the engine."
        detailed = (
            "The temperature is 220°F and the oil pressure is 5 PSI. "
            "The thermostat may be stuck closed at 195°F rating. "
            "Replace the 52mm thermostat and check the 1.5 inch hose."
        )
        r1 = evaluator.evaluate(vague, EXPECTED_KEYWORDS, scenario, "engine_diagnosis")
        r2 = evaluator.evaluate(detailed, EXPECTED_KEYWORDS, scenario, "engine_diagnosis")
        assert r2.specificity > r1.specificity

    def test_reasoning_detected(self, evaluator, scenario):
        no_reasoning = "Thermostat is broken. Replace it."
        with_reasoning = (
            "Because the upper hose is hot but the lower is cool, "
            "and since the coolant level is normal, the thermostat "
            "must be stuck closed. Therefore, replace it."
        )
        r1 = evaluator.evaluate(no_reasoning, EXPECTED_KEYWORDS, scenario, "engine_diagnosis")
        r2 = evaluator.evaluate(with_reasoning, EXPECTED_KEYWORDS, scenario, "engine_diagnosis")
        assert r2.reasoning > r1.reasoning

    def test_completeness_increases_with_structure(self, evaluator, scenario):
        short = "Thermostat stuck."
        long_structured = (
            "The diagnosis is a stuck thermostat.\n\n"
            "1. First, shut down the engine\n"
            "2. Remove the housing\n"
            "3. Replace the thermostat\n"
            "4. Refill coolant\n"
            "5. Test the system\n\n"
            "This will resolve the overheating issue because the new "
            "thermostat will allow proper coolant circulation throughout "
            "the engine block, maintaining the design temperature."
        )
        r1 = evaluator.evaluate(short, EXPECTED_KEYWORDS, scenario, "engine_diagnosis")
        r2 = evaluator.evaluate(long_structured, EXPECTED_KEYWORDS, scenario, "engine_diagnosis")
        assert r2.completeness > r1.completeness

    def test_pass_threshold_override(self, good_response, scenario):
        strict_eval = Evaluator(pass_threshold=0.95)
        result = strict_eval.evaluate(
            response=good_response,
            expected_keywords=EXPECTED_KEYWORDS,
            scenario=scenario,
            task_type="engine_diagnosis",
        )
        # Even a good response shouldn't pass 0.95
        assert not result.passed

    def test_composite_is_weighted_average(self, evaluator, good_response, scenario):
        result = evaluator.evaluate(
            response=good_response,
            expected_keywords=EXPECTED_KEYWORDS,
            scenario=scenario,
            task_type="engine_diagnosis",
        )
        expected = (
            result.accuracy * Evaluator.WEIGHTS["accuracy"]
            + result.specificity * Evaluator.WEIGHTS["specificity"]
            + result.reasoning * Evaluator.WEIGHTS["reasoning"]
            + result.completeness * Evaluator.WEIGHTS["completeness"]
        )
        assert abs(result.composite - round(expected, 3)) < 0.01

    def test_to_dict(self, evaluator, good_response, scenario):
        result = evaluator.evaluate(
            response=good_response,
            expected_keywords=EXPECTED_KEYWORDS,
            scenario=scenario,
            task_type="engine_diagnosis",
        )
        d = result.to_dict()
        assert "accuracy" in d
        assert "composite" in d
        assert "passed" in d
        assert "matched_keywords" in d
        assert isinstance(d["matched_keywords"], list)
