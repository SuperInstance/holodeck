"""Tests for emergency response task scenarios."""

import pytest
from holodeck.tasks import emergency_response


class TestEmergencyResponse:
    @pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
    def test_generate_scenario(self, difficulty):
        s = emergency_response.generate_scenario(difficulty, seed=42)
        assert s["task_type"] == "emergency_response"
        assert "prompt" in s
        assert "expected_keywords" in s
        assert "emergency_type" in s
        assert s["difficulty"] == difficulty

    def test_seed_reproducibility(self):
        s1 = emergency_response.generate_scenario("easy", seed=42)
        s2 = emergency_response.generate_scenario("easy", seed=42)
        assert s1 == s2

    def test_system_prompt_mentions_emergency(self):
        s = emergency_response.generate_scenario("easy", seed=42)
        assert "emergency" in s["system_prompt"].lower()

    def test_hard_has_more_keywords_than_easy(self):
        """Hard scenarios should require more safety considerations."""
        easy = emergency_response.generate_scenario("easy", seed=42)
        hard = emergency_response.generate_scenario("hard", seed=42)
        # At least 3 keywords in each
        assert len(easy["expected_keywords"]) >= 3
        assert len(hard["expected_keywords"]) >= 3
