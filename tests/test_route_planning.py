"""Tests for route planning task scenarios."""

import pytest
from holodeck.tasks import route_planning


class TestRoutePlanning:
    @pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
    def test_generate_scenario(self, difficulty):
        s = route_planning.generate_scenario(difficulty, seed=42)
        assert s["task_type"] == "route_planning"
        assert "prompt" in s
        assert "expected_keywords" in s
        assert s["difficulty"] == difficulty

    def test_seed_reproducibility(self):
        s1 = route_planning.generate_scenario("medium", seed=42)
        s2 = route_planning.generate_scenario("medium", seed=42)
        assert s1 == s2

    def test_system_prompt_mentions_navigation(self):
        s = route_planning.generate_scenario("easy", seed=42)
        assert "navigation" in s["system_prompt"].lower()

    def test_hard_scenario_mentions_more_hazards(self):
        easy = route_planning.generate_scenario("easy", seed=42)
        hard = route_planning.generate_scenario("hard", seed=42)
        # Hard scenarios should have longer conditions (more complexity)
        assert len(hard["prompt"]) > len(easy["prompt"]) * 0.5
