"""Tests for material selection task scenarios."""

import pytest
from holodeck.tasks import material_selection


class TestMaterialSelection:
    @pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
    def test_generate_scenario(self, difficulty):
        s = material_selection.generate_scenario(difficulty, seed=42)
        assert s["task_type"] == "material_selection"
        assert "prompt" in s
        assert "expected_keywords" in s
        assert s["difficulty"] == difficulty

    def test_seed_reproducibility(self):
        s1 = material_selection.generate_scenario("easy", seed=42)
        s2 = material_selection.generate_scenario("easy", seed=42)
        assert s1 == s2

    def test_system_prompt_mentions_engineering(self):
        s = material_selection.generate_scenario("easy", seed=42)
        assert "engineering" in s["system_prompt"].lower()
