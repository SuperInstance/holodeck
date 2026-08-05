"""Tests for the session reporter."""

import json
import pytest
from pathlib import Path
from holodeck.reporter import SessionReport
from holodeck.simulator import SimulationResult
from holodeck.evaluator import EvalResult


def _make_result(task_type, difficulty, passed, composite=0.5, accuracy=0.5):
    ev = EvalResult(
        accuracy=accuracy,
        specificity=0.4,
        reasoning=0.3,
        completeness=0.5,
        composite=composite,
        passed=passed,
        matched_keywords=["thermostat"],
        missed_keywords=["coolant"],
    )
    return SimulationResult(
        task_type=task_type,
        difficulty=difficulty,
        scenario={},
        response="test response",
        eval_result=ev,
        reflex_compiled=passed,
        response_time_ms=100,
    )


@pytest.fixture
def mixed_results():
    return [
        _make_result("engine_diagnosis", "easy", True, 0.7),
        _make_result("engine_diagnosis", "easy", False, 0.2),
        _make_result("route_planning", "medium", True, 0.6),
        _make_result("fish_id", "hard", False, 0.3),
        _make_result("material_selection", "easy", True, 0.8),
    ]


class TestSessionReport:
    def test_overall_stats(self, mixed_results):
        report = SessionReport(mixed_results)
        assert report.total == 5
        assert report.passed == 3
        assert report.failed == 2
        assert report.pass_rate == 0.6

    def test_by_type_breakdown(self, mixed_results):
        report = SessionReport(mixed_results)
        assert "engine_diagnosis" in report.by_type
        assert report.by_type["engine_diagnosis"]["total"] == 2
        assert report.by_type["engine_diagnosis"]["passed"] == 1
        assert report.by_type["route_planning"]["passed"] == 1

    def test_by_difficulty_breakdown(self, mixed_results):
        report = SessionReport(mixed_results)
        assert "easy" in report.by_difficulty
        assert "medium" in report.by_difficulty
        assert "hard" in report.by_difficulty
        assert report.by_difficulty["easy"]["total"] == 3

    def test_weakest_strongest_type(self, mixed_results):
        report = SessionReport(mixed_results)
        assert report.strongest_type[0] == "material_selection"
        assert report.weakest_type[0] == "fish_id"

    def test_missed_keywords_collected(self, mixed_results):
        report = SessionReport(mixed_results)
        assert "coolant" in report.missed_keywords
        # Each result missed "coolant"
        assert report.missed_keywords["coolant"] == 5

    def test_render_text_not_empty(self, mixed_results):
        report = SessionReport(mixed_results)
        text = report.render_text()
        assert "HOLODECK SESSION REPORT" in text
        assert "OVERALL" in text
        assert "BY TASK TYPE" in text
        assert "RECOMMENDATION" in text

    def test_to_dict(self, mixed_results):
        report = SessionReport(mixed_results)
        d = report.to_dict()
        assert d["total"] == 5
        assert d["passed"] == 3
        assert "by_type" in d
        assert "missed_keywords" in d

    def test_save_to_file(self, mixed_results, tmp_path):
        report = SessionReport(mixed_results)
        path = tmp_path / "report.json"
        report.save(path)
        assert path.exists()
        data = json.loads(path.read_text())
        assert data["total"] == 5

    def test_empty_results(self):
        report = SessionReport([])
        assert report.total == 0
        assert report.pass_rate == 0
        text = report.render_text()
        assert "HOLODECK SESSION REPORT" in text

    def test_reflex_count(self, mixed_results):
        report = SessionReport(mixed_results)
        assert report.reflexes_compiled == 3  # passed results compile reflexes
