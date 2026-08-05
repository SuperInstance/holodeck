"""
Engine Diagnosis Task — given symptoms, identify the problem.

Scenario generator produces varied engine problems with realistic symptoms.
Evaluator checks for correct diagnosis and appropriate troubleshooting steps.

Difficulty curve:
  easy:   Single failure, obvious symptoms
  medium: Multiple symptoms, some red herrings
  hard:   Intermittent / compound failures
"""

from __future__ import annotations

import random
from typing import Any

# ─── Problem Bank ──────────────────────────────────────────────

PROBLEMS = {
    "overheating_thermostat": {
        "name": "Stuck Thermostat (Overheating)",
        "difficulty_variants": {
            "easy": {
                "symptoms": (
                    "Engine temperature is climbing to 220°F and above. "
                    "The coolant level is normal. The raw water intake is clear. "
                    "There is no visible leak. The temperature rises steadily "
                    "even at idle."
                ),
                "diagnosis": "The thermostat is stuck closed, preventing coolant circulation.",
                "expected_keywords": [
                    "thermostat", "stuck closed", "coolant", "circulation",
                    "replace", "overheating",
                ],
            },
            "medium": {
                "symptoms": (
                    "Engine reaches 210°F after 15 minutes of operation. "
                    "Coolant level is full. Raw water strainer is clean. "
                    "You notice the upper radiator hose is hot but the lower "
                    "hose is cool to the touch. No steam visible yet."
                ),
                "diagnosis": "Thermostat stuck closed — restricted coolant flow confirmed by hose temperature differential.",
                "expected_keywords": [
                    "thermostat", "stuck closed", "hose", "temperature",
                    "differential", "replace", "coolant flow",
                ],
            },
            "hard": {
                "symptoms": (
                    "Engine runs at normal temperature for 20 minutes, then "
                    "spikes to 230°F over 5 minutes. Cycle repeats after cool-down. "
                    "Coolant is at proper level. Raw water flow appears normal. "
                    "Heat exchanger was serviced 50 hours ago. No external leaks."
                ),
                "diagnosis": "Thermostat intermittently sticking — possibly combined with early heat exchanger fouling.",
                "expected_keywords": [
                    "thermostat", "intermittent", "sticking", "heat exchanger",
                    "fouling", "flush", "replace thermostat",
                ],
            },
        },
    },
    "oil_pressure_drop": {
        "name": "Low Oil Pressure",
        "difficulty_variants": {
            "easy": {
                "symptoms": (
                    "Oil pressure gauge reads 5 PSI at idle (normal is 30+). "
                    "Engine has proper oil level. There is a visible oil leak "
                    "near the oil filter housing."
                ),
                "diagnosis": "Oil filter is loose or gasket failed, causing pressure loss.",
                "expected_keywords": [
                    "oil filter", "leak", "pressure", "gasket",
                    "tighten", "replace filter",
                ],
            },
            "medium": {
                "symptoms": (
                    "Oil pressure drops from 40 PSI to 15 PSI when engine warms up. "
                    "Oil level is between min and max. No visible leaks. "
                    "Engine has 2,000 hours since last oil change. You hear a "
                    "faint ticking from the valve cover."
                ),
                "diagnosis": "Worn main bearings causing oil pressure loss at operating temperature, or degraded oil viscosity.",
                "expected_keywords": [
                    "bearings", "worn", "oil viscosity", "oil change",
                    "warm", "pressure drop", "ticking",
                ],
            },
            "hard": {
                "symptoms": (
                    "Oil pressure fluctuates between 10 and 35 PSI at constant RPM. "
                    "No correlation with engine temperature. Oil level is normal. "
                    "Recent oil change 10 hours ago with correct grade. "
                    "Mechanical gauge confirms the reading."
                ),
                "diagnosis": "Oil pressure relief valve sticking, or oil pickup tube seal allowing air ingestion.",
                "expected_keywords": [
                    "relief valve", "pickup tube", "air ingestion",
                    "fluctuating", "pressure", "seal",
                ],
            },
        },
    },
    "fuel_starvation": {
        "name": "Fuel Starvation",
        "difficulty_variants": {
            "easy": {
                "symptoms": (
                    "Engine sputters and loses RPM under load but idles fine. "
                    "Fuel tank shows 1/4 full. Primary fuel filter has not been "
                    "changed in 200 hours."
                ),
                "diagnosis": "Clogged primary fuel filter restricting fuel flow under load.",
                "expected_keywords": [
                    "fuel filter", "clogged", "replace", "restriction",
                    "primary filter", "fuel flow",
                ],
            },
            "medium": {
                "symptoms": (
                    "Engine runs smoothly at idle but starves under throttle above 2000 RPM. "
                    "Fuel filters were replaced 50 hours ago. Tank has ample fuel. "
                    "You notice the lift pump makes an unusual clicking sound."
                ),
                "diagnosis": "Failing lift pump unable to maintain fuel pressure under demand.",
                "expected_keywords": [
                    "lift pump", "fuel pressure", "starving", "throttle",
                    "replace pump", "fuel delivery",
                ],
            },
            "hard": {
                "symptoms": (
                    "Engine intermittently cuts out for 2-3 seconds, then resumes. "
                    "Happens at random intervals, warm or cold. Filters are new. "
                    "Lift pump tests good. Tank vent is clear. You suspect an "
                    "electrical issue with the fuel solenoid."
                ),
                "diagnosis": "Fuel solenoid losing connection intermittently, or air ingress at a fitting.",
                "expected_keywords": [
                    "solenoid", "electrical", "connection", "air ingress",
                    "fitting", "intermittent", "wiring",
                ],
            },
        },
    },
    "raw_water_failure": {
        "name": "Raw Water Intake Failure",
        "difficulty_variants": {
            "easy": {
                "symptoms": (
                    "No water coming out of the exhaust. Engine temperature rising. "
                    "Raw water seacock is open. Strainer basket is full of debris."
                ),
                "diagnosis": "Clogged raw water strainer blocking intake flow.",
                "expected_keywords": [
                    "strainer", "clogged", "clean", "raw water",
                    "debris", "seacock",
                ],
            },
            "medium": {
                "symptoms": (
                    "Reduced water flow from exhaust. Engine running warm at 195°F. "
                    "Strainer is clean. Seacock is open. Impeller was replaced "
                    "200 hours ago (recommended interval is 100 hours)."
                ),
                "diagnosis": "Raw water pump impeller worn or damaged, reducing flow.",
                "expected_keywords": [
                    "impeller", "worn", "replace", "raw water pump",
                    "100 hours", "damaged",
                ],
            },
            "hard": {
                "symptoms": (
                    "Intermittent raw water flow. Engine temp fluctuates between "
                    "170°F and 205°F. Strainer clean, impeller is new (10 hours). "
                    "Hose from seacock to pump feels soft and spongy."
                ),
                "diagnosis": "Deteriorated intake hose collapsing under suction, or air leak at hose fitting.",
                "expected_keywords": [
                    "hose", "collapsing", "deteriorated", "suction",
                    "air leak", "fitting", "replace hose",
                ],
            },
        },
    },
    "alternator_failure": {
        "name": "Charging System Failure",
        "difficulty_variants": {
            "easy": {
                "symptoms": (
                    "Battery voltage reads 12.2V with engine running (should be 13.5-14.5V). "
                    "Charge warning light is on. Belt is intact and properly tensioned."
                ),
                "diagnosis": "Alternator has failed — not producing charge current.",
                "expected_keywords": [
                    "alternator", "charging", "voltage", "regulator",
                    "replace", "not charging",
                ],
            },
            "medium": {
                "symptoms": (
                    "Voltage reads 13.8V at idle but drops to 12.5V at higher RPM. "
                    "Belt is tight. Alternator is original (2,500 hours). "
                    "Batteries are 4 years old. Wiring connections look clean."
                ),
                "diagnosis": "Alternator diode failure or voltage regulator breakdown under load.",
                "expected_keywords": [
                    "diode", "regulator", "load", "alternator",
                    "voltage drop", "replace", "test",
                ],
            },
            "hard": {
                "symptoms": (
                    "Charging voltage fluctuates between 12V and 15V unpredictably. "
                    "No pattern with RPM. Battery shows signs of overcharging "
                    "(electrolyte loss). Belt, alternator, and regulator are each "
                    "less than 1 year old."
                ),
                "diagnosis": "Wiring harness corrosion causing intermittent high-resistance connections in the charging circuit.",
                "expected_keywords": [
                    "wiring", "corrosion", "resistance", "connection",
                    "harness", "voltage fluctuation", "inspect",
                ],
            },
        },
    },
}

# ─── Prompt Construction ───────────────────────────────────────

SYSTEM_PROMPT = (
    "You are Wesley, an engineering ensign on a fishing vessel. "
    "You are given engine symptoms and must diagnose the problem. "
    "Be specific. Name the likely cause, the reasoning behind your diagnosis, "
    "and the recommended action. Keep your response under 300 words."
)


def generate_scenario(difficulty: str = "easy", seed: int | None = None) -> dict[str, Any]:
    """
    Generate an engine diagnosis scenario.

    Args:
        difficulty: "easy", "medium", or "hard"
        seed: Optional random seed for reproducibility

    Returns:
        Scenario dict with prompt, expected_keywords, answer, metadata
    """
    rng = random.Random(seed)

    problem_keys = list(PROBLEMS.keys())
    rng.shuffle(problem_keys)
    problem_key = problem_keys[0]
    problem = PROBLEMS[problem_key]

    variant = problem["difficulty_variants"].get(difficulty, problem["difficulty_variants"]["easy"])

    prompt = (
        f"ENGINE DIAGNOSIS TASK ({difficulty.upper()})\n\n"
        f"Symptoms: {variant['symptoms']}\n\n"
        f"Diagnose the problem. State your diagnosis, explain your reasoning, "
        f"and recommend the corrective action."
    )

    return {
        "task_type": "engine_diagnosis",
        "prompt": prompt,
        "system_prompt": SYSTEM_PROMPT,
        "expected_keywords": variant["expected_keywords"],
        "correct_answer": variant["diagnosis"],
        "difficulty": difficulty,
        "problem_name": problem["name"],
        "problem_key": problem_key,
    }


def list_problems() -> list[str]:
    """Return available problem names."""
    return [p["name"] for p in PROBLEMS.values()]
