"""
Material Selection Task — given build requirements, choose materials.

Scenario generator produces engineering/build challenges.
Evaluator checks for appropriate material choices with sound reasoning.

Difficulty curve:
  easy:   Common application, clear requirements
  medium: Conflicting requirements (weight vs strength, cost vs durability)
  hard:   Multi-constraint optimization with environmental factors
"""

from __future__ import annotations

import random
from typing import Any

# ─── Scenario Bank ─────────────────────────────────────────────

SCENARIOS = {
    "hull_repair": {
        "difficulty_variants": {
            "easy": {
                "requirements": (
                    "Repair a 2-foot crack in a fiberglass hull above the "
                    "waterline. The boat is used in saltwater. The repair "
                    "must be watertight and structural."
                ),
                "expected_keywords": [
                    "fiberglass", "resin", "epoxy", "mat", "cloth",
                    "grind", "layup", "barrier coat", "gelcoat",
                ],
            },
            "medium": {
                "requirements": (
                    "Reinforce the transom of a 28-foot fishing boat that "
                    "will carry a heavier outboard (300hp vs original 225hp). "
                    "Transom is currently plywood-cored fiberglass. Budget is "
                    "moderate. Must handle increased torque and weight."
                ),
                "expected_keywords": [
                    "marine plywood", "fiberglass", "epoxy",
                    "core", "transom", "reinforcement", "layup",
                    "stiffness", "seal", "moisture",
                ],
            },
            "hard": {
                "requirements": (
                    "Design a custom fish hold liner for a commercial longliner. "
                    "Requirements: maintains 28°F with 2-inch insulation, "
                    "FDA-approved food-grade surface, withstands brine and fish "
                    "scales, must be repairable at sea, weight matters (vessel "
                    "has weight sensitivity), must fit through a 24-inch hatch. "
                    "Budget is flexible but not unlimited."
                ),
                "expected_keywords": [
                    "polyethylene", "HDPE", "closed-cell foam",
                    "insulation", "food-grade", "fiberglass",
                    "epoxy", "modular", "panels", "seams",
                    "urethane", "barrier", "thermal",
                ],
            },
        },
    },
    "deck_hardware": {
        "difficulty_variants": {
            "easy": {
                "requirements": (
                    "Select material for a new cleat backing plate inside a "
                    "fiberglass deck. The cleat is used for docking lines "
                    "under normal loads on a 30-foot vessel."
                ),
                "expected_keywords": [
                    "stainless steel", "aluminum", "backing plate",
                    "marine grade", "316", "pad", "load",
                    "distribution", "corrosion",
                ],
            },
            "medium": {
                "requirements": (
                    "Choose materials for a custom T-top frame on a center "
                    "console fishing boat. Must be corrosion-resistant, "
                    "lightweight enough not to affect stability, strong "
                    "enough to support radar and outriggers, and weldable "
                    "in the field. Budget is moderate."
                ),
                "expected_keywords": [
                    "aluminum", "6061", "anodized", "weldable",
                    "stainless", "hardware", "T-top", "corrosion",
                    "weight", "strength",
                ],
            },
            "hard": {
                "requirements": (
                    "Design a pot hauler mount that will be welded to the rail "
                    "of a steel-hull crabber. Must handle 500-pound vertical "
                    "loads with shock loading. Operating environment is "
                    "Bering Sea — ice, salt spray, freeze-thaw cycles. "
                    "Must be repairable by welding at sea. Vibration is severe. "
                    "Cannot drill extra holes in the existing rail."
                ),
                "expected_keywords": [
                    "steel", "mild steel", "A36", "welding",
                    "gusset", "bracket", "load", "shock",
                    "vibration", "corrosion", "coating",
                    "sacrificial", "anode", "clamp",
                ],
            },
        },
    },
    "piping_repair": {
        "difficulty_variants": {
            "easy": {
                "requirements": (
                    "Replace a cracked engine cooling water intake hose. "
                    "The hose carries raw saltwater at 5-10 PSI. Inner "
                    "diameter is 1.5 inches. Must last years without degradation."
                ),
                "expected_keywords": [
                    "marine hose", "reinforced", "raw water",
                    "wire reinforced", "neoprene", "EPDM",
                    "hose clamps", "double", "316 stainless",
                ],
            },
            "medium": {
                "requirements": (
                    "Run a new fuel supply line from the aft tank to the "
                    "forward engine room. Distance is 20 feet, through a "
                    "lazarette with limited access. Must be fire-resistant, "
                    "USCG-approved, and resist vibration. Diesel fuel, "
                    "not gasoline."
                ),
                "expected_keywords": [
                    "USCG", "Type A1", "fuel hose", "fire resistant",
                    "diesel", "copper", " tubing", "flare",
                    "fittings", "316", "rated", "vibration",
                ],
            },
            "hard": {
                "requirements": (
                    "Design a hydraulic line routing for a new deck crane. "
                    "System pressure is 3000 PSI. Lines must run 40 feet through "
                    "a fish hold maintained at 28°F, then through the engine room "
                    "at 120°F. Must withstand thermal cycling, vibration, and "
                    "occasional fish impact. Leak detection is critical — "
                    "hydraulic fluid in the fish hold is catastrophic."
                ),
                "expected_keywords": [
                    "hydraulic", "hose", "3000 PSI", "rated",
                    "thermal", "insulation", "stainless",
                    "braided", "jic", "fittings", "leak",
                    "detection", "secondary", "containment",
                    "barrier", "routing",
                ],
            },
        },
    },
}

SYSTEM_PROMPT = (
    "You are Wesley, a marine engineering assistant. "
    "You are given material selection requirements for a marine application. "
    "Recommend specific materials, explain why each is appropriate, and note "
    "any alternatives considered and rejected. Address durability, maintenance, "
    "and safety. Keep your response under 300 words."
)


def generate_scenario(difficulty: str = "easy", seed: int | None = None) -> dict[str, Any]:
    """
    Generate a material selection scenario.

    Args:
        difficulty: "easy", "medium", or "hard"
        seed: Optional random seed for reproducibility
    """
    rng = random.Random(seed)
    scenario_keys = list(SCENARIOS.keys())
    rng.shuffle(scenario_keys)
    scenario_key = scenario_keys[0]
    scenario = SCENARIOS[scenario_key]

    variant = scenario["difficulty_variants"].get(difficulty, scenario["difficulty_variants"]["easy"])

    prompt = (
        f"MATERIAL SELECTION TASK ({difficulty.upper()})\n\n"
        f"Requirements: {variant['requirements']}\n\n"
        f"Recommend the best materials for this application. Explain your "
        f"choices, address tradeoffs, and note safety considerations."
    )

    return {
        "task_type": "material_selection",
        "prompt": prompt,
        "system_prompt": SYSTEM_PROMPT,
        "expected_keywords": variant["expected_keywords"],
        "correct_answer": "(evaluated on material knowledge and reasoning)",
        "difficulty": difficulty,
        "scenario_name": scenario_key,
    }
