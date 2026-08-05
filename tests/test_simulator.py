"""Tests for the main holodeck simulator."""

import json
import pytest
from pathlib import Path
from holodeck.simulator import HolodeckSimulator, SimulationResult, mock_response, compile_reflex, update_weakness_map
from holodeck.evaluator import Evaluator, EvalResult


@pytest.fixture
def simulator():
    return HolodeckSimulator(dry_run=True)


class TestHolodeckSimulator:
    def test_dry_run_single_task(self, simulator):
        result = simulator.run_single("engine_diagnosis", "easy", seed=42)
        assert isinstance(result, SimulationResult)
        assert result.task_type == "engine_diagnosis"
        assert result.difficulty == "easy"
        assert len(result.response) > 0
        assert result.response_time_ms > 0

    def test_dry_run_session_10_tasks(self, simulator):
        results = simulator.run_session(tasks=10, seed_offset=42)
        assert len(results) == 10
        # Should rotate through task types
        task_types = {r.task_type for r in results}
        assert len(task_types) >= 3  # At least 3 different types

    def test_dry_run_all_5_types(self, simulator):
        results = simulator.run_session(tasks=5, seed_offset=0)
        task_types = {r.task_type for r in results}
        assert task_types == {"engine_diagnosis", "route_planning", "fish_id", "material_selection", "emergency_response"}

    def test_dry_run_difficulty_escalation(self, simulator):
        results = simulator.run_session(tasks=9, seed_offset=0)
        # First 3 should be easy, next 3 medium, last 3 hard
        difficulties = [r.difficulty for r in results]
        assert difficulties[0] == "easy"
        assert difficulties[4] == "medium"
        assert difficulties[8] == "hard"

    def test_dry_run_no_crash_on_all_task_types(self, simulator):
        """Must run across all 5 types without crashing."""
        for tt in ["engine_diagnosis", "route_planning", "fish_id", "material_selection", "emergency_response"]:
            result = simulator.run_single(tt, "medium", seed=42)
            assert result.task_type == tt
            assert result.eval_result.composite >= 0

    def test_session_saves_to_file(self, simulator, tmp_path, monkeypatch):
        monkeypatch.setattr("holodeck.simulator.SESSION_DIR", tmp_path)
        results = simulator.run_session(tasks=3, seed_offset=0)
        path = simulator.save_session(results)
        assert path.exists()
        lines = path.read_text().strip().split("\n")
        assert len(lines) == 3
        for line in lines:
            data = json.loads(line)
            assert "task_type" in data
            assert "eval" in data

    def test_mock_response_returns_text(self):
        scenario = {
            "prompt": "test",
            "correct_answer": "thermostat stuck closed",
            "expected_keywords": ["thermostat", "replace"],
        }
        resp = mock_response(scenario)
        assert isinstance(resp, str)
        assert len(resp) > 20

    def test_compile_reflex_on_pass(self, tmp_path, monkeypatch):
        monkeypatch.setattr("holodeck.simulator.REFLEX_DIR", tmp_path)
        scenario = {"difficulty": "easy", "problem_name": "test"}
        response = "Good response with thermostat and coolant details."
        ev = EvalResult(
            accuracy=0.8, specificity=0.6, reasoning=0.5,
            completeness=0.7, composite=0.65, passed=True,
        )
        result = compile_reflex("engine_diagnosis", scenario, response, ev)
        assert result["compiled"] is True
        assert len(result["nail_id"]) == 16
        nail_path = Path(result["path"])
        assert nail_path.exists()
        nail = json.loads(nail_path.read_text())
        assert nail["task_type"] == "engine_diagnosis"
        assert nail["outcome"] == "success"

    def test_update_weakness_map(self, tmp_path, monkeypatch):
        monkeypatch.setattr("holodeck.simulator.WEAKNESS_MAP_PATH", tmp_path / "weakness.json")
        from holodeck.tasks import TASK_NAMES

        results = []
        for tt in ["engine_diagnosis", "fish_id", "engine_diagnosis"]:
            ev = EvalResult(
                accuracy=0.5, specificity=0.4, reasoning=0.3,
                completeness=0.4, composite=0.4, passed=False,
            )
            results.append(SimulationResult(
                task_type=tt, difficulty="easy", scenario={}, response="test",
                eval_result=ev,
            ))

        wm = update_weakness_map(results)
        assert "engine_diagnosis" in wm
        assert wm["engine_diagnosis"]["total"] == 2
        assert wm["fish_id"]["total"] == 1
        assert wm["engine_diagnosis"]["pass_rate"] == 0.0

    def test_threshold_override(self):
        strict_sim = HolodeckSimulator(pass_threshold=0.99, dry_run=True)
        result = strict_sim.run_single("engine_diagnosis", "easy", seed=42)
        # Mock responses shouldn't pass 0.99
        assert not result.eval_result.passed

    def test_simulation_result_to_dict(self, simulator):
        result = simulator.run_single("engine_diagnosis", "easy", seed=42)
        d = result.to_dict()
        assert "task_type" in d
        assert "eval" in d
        assert "response" in d
        assert isinstance(d["eval"]["matched_keywords"], list)
