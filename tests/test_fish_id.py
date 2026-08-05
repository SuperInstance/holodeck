"""Tests for fish identification task scenarios."""

import pytest
from holodeck.tasks import fish_id


class TestFishID:
    @pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
    def test_generate_scenario(self, difficulty):
        s = fish_id.generate_scenario(difficulty, seed=42)
        assert s["task_type"] == "fish_id"
        assert "prompt" in s
        assert "expected_keywords" in s
        assert "species_name" in s
        assert s["difficulty"] == difficulty

    def test_seed_reproducibility(self):
        s1 = fish_id.generate_scenario("easy", seed=42)
        s2 = fish_id.generate_scenario("easy", seed=42)
        assert s1 == s2

    def test_system_prompt_mentions_fisheries(self):
        s = fish_id.generate_scenario("easy", seed=42)
        assert "fisher" in s["system_prompt"].lower() or "observer" in s["system_prompt"].lower()

    def test_species_name_in_keywords(self):
        """The species common name should be in expected keywords."""
        for _ in range(5):
            s = fish_id.generate_scenario("easy", seed=None)
            name_lower = s["species_name"].split("(")[0].strip().lower()
            assert name_lower in [kw.lower() for kw in s["expected_keywords"]]
