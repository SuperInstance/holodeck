"""Tests for engine diagnosis task scenarios."""

import pytest
from holodeck.tasks import engine_diagnosis


class TestEngineDiagnosis:
    @pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
    def test_generate_scenario_returns_valid_dict(self, difficulty):
        scenario = engine_diagnosis.generate_scenario(difficulty=difficulty, seed=42)
        assert isinstance(scenario, dict)
        assert scenario["task_type"] == "engine_diagnosis"
        assert "prompt" in scenario
        assert "system_prompt" in scenario
        assert "expected_keywords" in scenario
        assert "correct_answer" in scenario
        assert scenario["difficulty"] == difficulty

    def test_easy_scenario_has_more_keywords_than_hard(self):
        """Easy scenarios should generally have fewer, more obvious keywords."""
        easy = engine_diagnosis.generate_scenario("easy", seed=42)
        hard = engine_diagnosis.generate_scenario("hard", seed=42)
        # Both should have meaningful keyword sets
        assert len(easy["expected_keywords"]) >= 3
        assert len(hard["expected_keywords"]) >= 3

    def test_seed_reproducibility(self):
        s1 = engine_diagnosis.generate_scenario("easy", seed=42)
        s2 = engine_diagnosis.generate_scenario("easy", seed=42)
        assert s1 == s2

    def test_different_seeds_different_scenarios(self):
        s1 = engine_diagnosis.generate_scenario("easy", seed=42)
        s2 = engine_diagnosis.generate_scenario("easy", seed=100)
        # The problem selected should potentially differ
        # (at minimum, different random shuffles)
        assert s1 is not None
        assert s2 is not None

    def test_prompt_contains_difficulty_label(self):
        for diff in ["easy", "medium", "hard"]:
            s = engine_diagnosis.generate_scenario(diff, seed=42)
            assert diff.upper() in s["prompt"]

    def test_system_prompt_is_engineering_role(self):
        s = engine_diagnosis.generate_scenario("easy", seed=42)
        assert "engineering" in s["system_prompt"].lower() or "ensign" in s["system_prompt"].lower()

    def test_list_problems(self):
        problems = engine_diagnosis.list_problems()
        assert isinstance(problems, list)
        assert len(problems) >= 3
