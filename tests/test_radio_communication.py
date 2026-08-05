"""
Tests for the Radio Communication task module.
"""

import pytest

from holodeck.tasks.radio_communication import (
    SCENARIOS,
    SYSTEM_PROMPT,
    generate_scenario,
)


class TestRadioCommunication:
    """Test the radio communication scenario generator."""

    @pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
    def test_generate_scenario(self, difficulty):
        """Each difficulty produces a valid scenario dict."""
        scenario = generate_scenario(difficulty=difficulty, seed=42)

        assert scenario["task_type"] == "radio_communication"
        assert scenario["difficulty"] == difficulty
        assert isinstance(scenario["prompt"], str)
        assert len(scenario["prompt"]) > 50
        assert isinstance(scenario["system_prompt"], str)
        assert len(scenario["system_prompt"]) > 20
        assert isinstance(scenario["expected_keywords"], list)
        assert len(scenario["expected_keywords"]) >= 5
        assert isinstance(scenario["correct_answer"], str)
        assert scenario["scenario_type"] in SCENARIOS

    def test_seed_reproducibility(self):
        """Same seed produces same scenario."""
        s1 = generate_scenario(difficulty="easy", seed=123)
        s2 = generate_scenario(difficulty="easy", seed=123)
        assert s1 == s2

    def test_different_seeds_may_differ(self):
        """Different seeds likely produce different scenarios."""
        prompts = set()
        for seed in range(20):
            s = generate_scenario(difficulty="easy", seed=seed)
            prompts.add(s["scenario_type"])
        # With 4 scenario categories and 20 seeds, we should see at least 2 different ones
        assert len(prompts) >= 2

    def test_system_prompt_mentions_radio(self):
        """System prompt should mention radio or communications."""
        assert "radio" in SYSTEM_PROMPT.lower() or "communication" in SYSTEM_PROMPT.lower()

    def test_system_prompt_mentions_terminology(self):
        """System prompt should reference proper maritime terminology."""
        prompt_lower = SYSTEM_PROMPT.lower()
        assert "mayday" in prompt_lower or "phonetic" in prompt_lower or "channel" in prompt_lower

    def test_hard_scenario_has_more_keywords(self):
        """Hard scenarios should generally have more keywords than easy."""
        # Run multiple times to account for randomization
        easy_counts = []
        hard_counts = []
        for seed in range(20):
            easy = generate_scenario(difficulty="easy", seed=seed)
            hard = generate_scenario(difficulty="hard", seed=seed)
            easy_counts.append(len(easy["expected_keywords"]))
            hard_counts.append(len(hard["expected_keywords"]))

        # On average, hard should have more
        assert sum(hard_counts) >= sum(easy_counts)

    def test_all_scenarios_have_four_categories(self):
        """Verify we have the expected scenario categories."""
        expected = {
            "routine_bridge_to_bridge",
            "distress_mayday",
            "pan_pan_medical",
            "digital_selective_calling",
        }
        assert set(SCENARIOS.keys()) == expected

    def test_all_scenarios_have_three_difficulties(self):
        """Each scenario must have easy, medium, hard variants."""
        for name, scenario in SCENARIOS.items():
            variants = scenario["difficulty_variants"]
            assert "easy" in variants, f"{name} missing easy"
            assert "medium" in variants, f"{name} missing medium"
            assert "hard" in variants, f"{name} missing hard"

    def test_scenario_prompt_includes_difficulty_label(self):
        """Prompt should contain the difficulty level."""
        for diff in ["easy", "medium", "hard"]:
            scenario = generate_scenario(difficulty=diff, seed=7)
            assert diff.upper() in scenario["prompt"]

    def test_scenario_prompt_includes_task_type(self):
        """Prompt should contain the task type name."""
        scenario = generate_scenario(difficulty="easy", seed=7)
        assert "RADIO COMMUNICATION TASK" in scenario["prompt"]

    def test_expected_keywords_are_strings(self):
        """All expected keywords should be strings."""
        for seed in range(10):
            scenario = generate_scenario(difficulty="medium", seed=seed)
            for kw in scenario["expected_keywords"]:
                assert isinstance(kw, str)
                assert len(kw) > 0

    def test_situation_text_is_substantive(self):
        """Each difficulty variant should have a real situation description."""
        for name, scenario in SCENARIOS.items():
            for diff, variant in scenario["difficulty_variants"].items():
                situation = variant["situation"]
                assert len(situation) > 50, f"{name}/{diff} situation too short"
