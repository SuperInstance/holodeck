"""Tests for the task registry."""

from holodeck.tasks import TASK_REGISTRY, TASK_NAMES, DIFFICULTIES


class TestTaskRegistry:
    def test_all_five_types_registered(self):
        expected = {
            "engine_diagnosis",
            "route_planning",
            "fish_id",
            "material_selection",
            "emergency_response",
        }
        assert set(TASK_REGISTRY.keys()) == expected

    def test_all_modules_have_generate_scenario(self):
        for name, module in TASK_REGISTRY.items():
            assert hasattr(module, "generate_scenario"), f"{name} missing generate_scenario"
            assert callable(module.generate_scenario), f"{name}.generate_scenario not callable"

    def test_all_modules_have_system_prompt(self):
        for name, module in TASK_REGISTRY.items():
            assert hasattr(module, "SYSTEM_PROMPT"), f"{name} missing SYSTEM_PROMPT"
            assert isinstance(module.SYSTEM_PROMPT, str)
            assert len(module.SYSTEM_PROMPT) > 10

    def test_task_names_match_keys(self):
        for key in TASK_REGISTRY:
            assert key in TASK_NAMES
            assert isinstance(TASK_NAMES[key], str)

    def test_difficulties_in_order(self):
        assert DIFFICULTIES == ["easy", "medium", "hard"]

    def test_generate_scenario_for_every_type_and_difficulty(self):
        for task_type, module in TASK_REGISTRY.items():
            for difficulty in DIFFICULTIES:
                s = module.generate_scenario(difficulty=difficulty, seed=42)
                assert s is not None
                assert s["task_type"] == task_type
                assert s["difficulty"] == difficulty
                assert len(s["expected_keywords"]) >= 3
