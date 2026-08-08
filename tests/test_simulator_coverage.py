"""
Tests for simulator bug fixes and additional coverage.

Covers:
- mock_response determinism (BUG-1: hash() was non-deterministic)
- log_failure direct test (gap: no direct coverage)
- compile_reflex full field validation
- call_ollama fallback behavior (mocked)
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from holodeck.simulator import (
    mock_response,
    log_failure,
    compile_reflex,
    HolodeckSimulator,
    SimulationResult,
    REFLEX_DIR,
    FAILURE_DIR,
)
from holodeck.evaluator import EvalResult


class TestMockResponseDeterminism:
    """BUG-1: mock_response must be deterministic for the same scenario."""

    def _make_scenario(self):
        return {
            "prompt": "ENGINE DIAGNOSIS TASK (EASY)\n\nSymptoms: overheating",
            "correct_answer": "Thermostat stuck closed.",
            "expected_keywords": ["thermostat", "coolant", "overheating", "replace"],
        }

    def test_same_scenario_same_response(self):
        """The same scenario dict must always produce the same mock response."""
        scenario = self._make_scenario()
        resp1 = mock_response(scenario)
        resp2 = mock_response(scenario)
        assert resp1 == resp2, "mock_response must be deterministic"

    def test_different_prompt_different_response(self):
        """Different prompts should (usually) produce different responses."""
        s1 = self._make_scenario()
        s2 = self._make_scenario()
        s2["prompt"] = "ROUTE PLANNING TASK (HARD)\n\nConditions: rough seas"
        # Not guaranteed to differ, but with different md5 seeds it's very likely
        assert mock_response(s1) != mock_response(s2)

    def test_deterministic_across_multiple_calls(self):
        """Call 10 times — all must return the same result."""
        scenario = self._make_scenario()
        responses = [mock_response(scenario) for _ in range(10)]
        assert len(set(responses)) == 1

    def test_mock_response_includes_correct_answer(self):
        """Mock response should reference the correct answer."""
        scenario = self._make_scenario()
        resp = mock_response(scenario)
        # The correct answer (truncated) should appear in the response
        assert scenario["correct_answer"][:20] in resp


class TestLogFailure:
    """Direct tests for log_failure function."""

    def test_log_failure_writes_jsonl(self, tmp_path, monkeypatch):
        """log_failure should append a JSON line to the task-specific file."""
        monkeypatch.setattr("holodeck.simulator.FAILURE_DIR", tmp_path)
        scenario = {
            "difficulty": "medium",
            "prompt": "Test prompt for failure",
        }
        ev = EvalResult(
            accuracy=0.2, specificity=0.1, reasoning=0.1,
            completeness=0.2, composite=0.15, passed=False,
            matched_keywords=["a"],
            missed_keywords=["b", "c", "d"],
        )
        log_failure("engine_diagnosis", scenario, "Bad response", ev)

        failure_file = tmp_path / "engine_diagnosis_failures.jsonl"
        assert failure_file.exists()
        lines = failure_file.read_text().strip().split("\n")
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["task_type"] == "engine_diagnosis"
        assert data["difficulty"] == "medium"
        assert data["prompt"] == "Test prompt for failure"
        assert data["response"] == "Bad response"
        assert data["missed_keywords"] == ["b", "c", "d"]

    def test_log_failure_appends_multiple(self, tmp_path, monkeypatch):
        """Multiple failures should append, not overwrite."""
        monkeypatch.setattr("holodeck.simulator.FAILURE_DIR", tmp_path)
        scenario = {"difficulty": "easy", "prompt": "p"}
        ev = EvalResult(
            accuracy=0.0, specificity=0.0, reasoning=0.0,
            completeness=0.0, composite=0.0, passed=False,
        )
        for i in range(3):
            log_failure("fish_id", scenario, f"response {i}", ev)

        failure_file = tmp_path / "fish_id_failures.jsonl"
        lines = failure_file.read_text().strip().split("\n")
        assert len(lines) == 3


class TestCompileReflexFields:
    """Validate all fields in the compiled .nail reflex."""

    def test_reflex_has_all_expected_fields(self, tmp_path, monkeypatch):
        monkeypatch.setattr("holodeck.simulator.REFLEX_DIR", tmp_path)
        scenario = {
            "difficulty": "hard",
            "problem_name": "Fuel Starvation",
        }
        response = "The lift pump is failing because of fuel starvation."
        ev = EvalResult(
            accuracy=0.9, specificity=0.7, reasoning=0.8,
            completeness=0.85, composite=0.81, passed=True,
            matched_keywords=["lift pump", "fuel starvation"],
            missed_keywords=["pressure"],
        )
        result = compile_reflex("engine_diagnosis", scenario, response, ev)

        nail_path = Path(result["path"])
        nail = json.loads(nail_path.read_text())

        # Check all expected fields
        assert nail["domain"] == "holodeck"
        assert nail["task_type"] == "engine_diagnosis"
        assert nail["outcome"] == "success"
        assert nail["outcome_quality"] == 0.81
        assert nail["scenario_detail"]["difficulty"] == "hard"
        assert nail["scenario_detail"]["problem_name"] == "Fuel Starvation"
        assert nail["response_excerpt"] == response[:500]
        assert nail["matched_keywords"] == ["lift pump", "fuel starvation"]
        assert nail["missed_keywords"] == ["pressure"]
        assert "accuracy" in nail["scores"]
        assert "specificity" in nail["scores"]
        assert "reasoning" in nail["scores"]
        assert "completeness" in nail["scores"]
        assert nail["metadata"]["source"] == "holodeck"
        assert "timestamp" in nail["metadata"]
        assert len(nail["id"]) == 16

    def test_reflex_id_is_unique(self, tmp_path, monkeypatch):
        """Different scenarios should produce different reflex IDs."""
        monkeypatch.setattr("holodeck.simulator.REFLEX_DIR", tmp_path)
        ev = EvalResult(
            accuracy=0.8, specificity=0.6, reasoning=0.5,
            completeness=0.7, composite=0.65, passed=True,
        )
        r1 = compile_reflex("engine_diagnosis", {"difficulty": "easy"}, "resp1", ev)
        # Force a different timestamp by patching time
        with patch("holodeck.simulator.time.time", return_value=999999.0):
            r2 = compile_reflex("fish_id", {"difficulty": "hard"}, "resp2", ev)
        assert r1["nail_id"] != r2["nail_id"]


class TestCallOllamaFallback:
    """Test call_ollama fallback behavior with mocking."""

    @patch("urllib.request.urlopen")
    @patch("holodeck.simulator.subprocess.run")
    def test_fallback_to_cli_on_api_failure(self, mock_subprocess, mock_urlopen):
        """If the API fails, should fall back to CLI."""
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

        mock_subprocess.return_value = MagicMock(
            returncode=0,
            stdout="The thermostat is stuck closed.",
            stderr="",
        )

        from holodeck.simulator import call_ollama
        text, elapsed = call_ollama("system", "user", timeout=5)
        assert "thermostat" in text
        assert elapsed >= 0
        mock_subprocess.assert_called_once()

    @patch("urllib.request.urlopen")
    @patch("holodeck.simulator.subprocess.run")
    def test_both_api_and_cli_failure_returns_error(self, mock_subprocess, mock_urlopen):
        """If both API and CLI fail, should return an error string, not crash."""
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")
        mock_subprocess.side_effect = FileNotFoundError("ollama not found")

        from holodeck.simulator import call_ollama
        text, elapsed = call_ollama("system", "user", timeout=5)
        assert "Error" in text
        assert elapsed >= 0
