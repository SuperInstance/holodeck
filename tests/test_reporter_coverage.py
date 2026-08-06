"""Tests for reporter.save() and additional edge cases."""

import json
import tempfile
from pathlib import Path

import pytest

from holodeck.evaluator import EvalResult
from holodeck.reporter import SessionReport
from holodeck.simulator import SimulationResult


def make_result(task_type="fish_id", difficulty="easy", composite=0.5, passed=True,
                response="Test response", reflex_compiled=False, response_time_ms=500):
    return SimulationResult(
        task_type=task_type,
        difficulty=difficulty,
        scenario={"prompt": "test"},
        response=response,
        eval_result=EvalResult(
            accuracy=0.5,
            specificity=0.5,
            reasoning=0.5,
            completeness=0.5,
            composite=composite,
            passed=passed,
            matched_keywords=["fish"],
            missed_keywords=["weight"],
        ),
        reflex_compiled=reflex_compiled,
        reflex_id="test-id" if reflex_compiled else "",
        timestamp="2026-01-01T00:00:00Z",
        response_time_ms=response_time_ms,
    )


class TestSessionReportSave:
    def test_save_creates_json_file(self, tmp_path):
        results = [make_result(), make_result(task_type="engine_diagnosis")]
        report = SessionReport(results)
        out = tmp_path / "report.json"
        report.save(out)
        assert out.exists()
        data = json.loads(out.read_text())
        assert isinstance(data, dict)
        assert "results" in data or "total" in data or "summary" in data

    def test_save_outputs_valid_json(self, tmp_path):
        results = [make_result()]
        report = SessionReport(results)
        out = tmp_path / "report.json"
        report.save(out)
        data = json.loads(out.read_text())
        assert isinstance(data, dict)

    def test_to_json_returns_string(self):
        results = [make_result()]
        report = SessionReport(results)
        s = report.to_json()
        assert isinstance(s, str)
        # Should be valid JSON
        json.loads(s)


class TestSessionReportRenderEdgeCases:
    def test_render_empty_results(self):
        report = SessionReport([])
        text = report.render_text()
        assert isinstance(text, str)

    def test_render_single_result(self):
        results = [make_result(composite=0.8, passed=True)]
        report = SessionReport(results)
        text = report.render_text()
        assert isinstance(text, str)
        assert len(text) > 0

    def test_render_all_failed(self):
        results = [
            make_result(composite=0.1, passed=False),
            make_result(task_type="engine_diagnosis", composite=0.2, passed=False),
        ]
        report = SessionReport(results)
        text = report.render_text()
        assert isinstance(text, str)

    def test_render_all_passed(self):
        results = [
            make_result(composite=0.9, passed=True),
            make_result(task_type="engine_diagnosis", composite=0.85, passed=True),
        ]
        report = SessionReport(results)
        text = report.render_text()
        assert isinstance(text, str)

    def test_render_mixed_results(self):
        results = [
            make_result(composite=0.9, passed=True),
            make_result(task_type="engine_diagnosis", composite=0.2, passed=False),
            make_result(task_type="radio_communication", composite=0.6, passed=True),
        ]
        report = SessionReport(results)
        text = report.render_text()
        assert isinstance(text, str)


class TestSessionReportAnalysis:
    def test_summary_has_expected_keys(self):
        results = [make_result()]
        report = SessionReport(results)
        assert hasattr(report, 'total')
        assert hasattr(report, 'passed')
        assert hasattr(report, 'failed')
        assert hasattr(report, 'pass_rate')
        assert hasattr(report, 'avg_score')

    def test_session_stats(self):
        results = [
            make_result(composite=0.8, passed=True, response_time_ms=500),
            make_result(task_type="engine_diagnosis", composite=0.4, passed=False, response_time_ms=800),
        ]
        report = SessionReport(results)
        assert report.total == 2
        assert report.passed == 1
        assert report.failed == 1

    def test_difficulty_breakdown(self):
        results = [
            make_result(difficulty="easy"),
            make_result(difficulty="easy"),
            make_result(difficulty="hard"),
        ]
        report = SessionReport(results)
        assert hasattr(report, 'by_difficulty')
        assert "easy" in report.by_difficulty
        assert "hard" in report.by_difficulty

    def test_reflex_compilation_count(self):
        results = [
            make_result(reflex_compiled=True),
            make_result(reflex_compiled=False),
            make_result(reflex_compiled=True),
        ]
        report = SessionReport(results)
        assert report.reflexes_compiled == 2


class TestSimulationResultSerialization:
    def test_to_dict_has_expected_keys(self):
        r = make_result()
        d = r.to_dict()
        assert "task_type" in d
        assert "difficulty" in d
        assert "response" in d
        assert "eval" in d
        assert "reflex_compiled" in d

    def test_to_dict_eval_is_dict(self):
        r = make_result()
        d = r.to_dict()
        assert isinstance(d["eval"], dict)
        assert "composite" in d["eval"]
        assert "passed" in d["eval"]


class TestSessionReportLargeSession:
    def test_20_results_different_types(self):
        types = ["fish_id", "engine_diagnosis", "radio_communication",
                 "emergency_response", "material_selection", "route_planning"]
        results = [
            make_result(task_type=types[i % len(types)], composite=0.3 + 0.1 * i)
            for i in range(20)
        ]
        report = SessionReport(results)
        text = report.render_text()
        assert isinstance(text, str)
        assert report.total == 20
        assert hasattr(report, 'weakest_type')
        assert hasattr(report, 'strongest_type')

    def test_100_results_performance(self):
        """Should handle 100 results without issue."""
        results = [make_result(composite=0.5 + 0.005 * i) for i in range(100)]
        report = SessionReport(results)
        text = report.render_text()
        assert len(text) > 0
