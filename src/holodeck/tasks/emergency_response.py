"""
Emergency Response Task — given situation, choose correct protocol.

Scenario generator produces maritime emergency scenarios.
Evaluator checks for correct protocol, appropriate actions, and safety priorities.

Difficulty curve:
  easy:   Common emergency, clear protocol
  medium: Time-critical with competing priorities
  hard:   Compound emergencies, ambiguous information
"""

from __future__ import annotations

import random
from typing import Any

# ─── Emergency Bank ────────────────────────────────────────────

EMERGENCIES = {
    "engine_room_fire": {
        "difficulty_variants": {
            "easy": {
                "situation": (
                    "Small fire in the engine room near the fuel filters. "
                    "You are 5 miles offshore with 3 crew aboard. "
                    "Engine is still running. Seas are calm."
                ),
                "expected_keywords": [
                    "shut down", "engine", "fuel", "extinguisher",
                    "CO2", "clean agent", "close", "vents",
                    "hatch", "do not open", "PFD",
                ],
            },
            "medium": {
                "situation": (
                    "Engine room fire with smoke visible from the galley sole. "
                    "You are 15 miles offshore in 4-foot seas. Two crew members "
                    "are forward. The fixed fire suppression system has a "
                    "manual release in the cockpit. One crew member is not "
                    "wearing a PFD."
                ),
                "expected_keywords": [
                    "muster", "PFD", "fixed", "system", "release",
                    "CO2", "shut down", "fuel", "close",
                    "vents", "wait", "do not open",
                    "boundary", "cooling", "mayday", "VHF",
                ],
            },
            "hard": {
                "situation": (
                    "Fire in the lazarette that has spread to the fuel tank "
                    "vent. You are 40 miles offshore in 8-foot seas at night. "
                    "Fixed suppression system discharged but fire is not out. "
                    "One crew member has burns on their hands. The liferaft "
                    "is mounted on the cabin top and may be exposed to heat. "
                    "Another vessel is 3 miles away and responding to your "
                    "mayday."
                ),
                "expected_keywords": [
                    "abandon", "liferaft", "burns", "first aid",
                    "mayday", "VHF", "16", "remaining",
                    "extinguishers", "boundary", "cooling",
                    "prepare", "transfer", "rescue",
                    "PFD", "immersion", "survival",
                ],
            },
        },
    },
    "flooding": {
        "difficulty_variants": {
            "easy": {
                "situation": (
                    "Bilge alarm sounds. Water rising in the bilge at a "
                    "moderate rate. You are in protected waters near a harbor. "
                    "Two bilge pumps are running but water level is not dropping."
                ),
                "expected_keywords": [
                    "source", "find", "leak", "through-hull",
                    "hose", "clamp", "dewater", "pump",
                    "plug", "wedge", "report", "harbor",
                ],
            },
            "medium": {
                "situation": (
                    "Rapid flooding from an unknown source. Water is above "
                    "the cabin sole in the galley. You are 10 miles offshore. "
                    "Both bilge pumps are overwhelmed. Engine intake is "
                    "threatened. Four crew aboard, one is injured (broken arm)."
                ),
                "expected_keywords": [
                    "find", "source", "through-hull", "plug",
                    "damage", "control", "dewater", "mayday",
                    "VHF", "16", "PFD", "prepare",
                    "abandon", "head", "harbor", "beach",
                ],
            },
            "hard": {
                "situation": (
                    "Collision with a submerged object has holed the bow "
                    "below the waterline. Water is flooding the forward cabin "
                    "and forecastle. Vessel is pitching heavily in 6-foot seas. "
                    "The hole is estimated at 8 inches diameter. You are 25 "
                    "miles offshore. Crew of 4. The vessel has collision "
                    "bulkhead but water is finding its way aft through "
                    "cable conduits."
                ),
                "expected_keywords": [
                    "collision", "bulkhead", "damage control",
                    "plug", "patch", "mattress", "blanket",
                    "wedge", "dewater", "pump", "mayday",
                    "VHF", "16", "PFD", "liferaft",
                    "ready", "aft", "seal", "conduit",
                    "trim", "slow", "steerage",
                ],
            },
        },
    },
    "man_overboard": {
        "difficulty_variants": {
            "easy": {
                "situation": (
                    "Crew member falls overboard while hauling gear. "
                    "Water temperature is 55°F. Seas are 2 feet. "
                    "You saw them go in. The vessel is making 5 knots."
                ),
                "expected_keywords": [
                    "throw", "life ring", "type IV", "call",
                    "spotter", "keep", "eyes", "turn",
                    "Williamson", "or", "quick stop",
                    "approach", "leeward", "recover",
                ],
            },
            "medium": {
                "situation": (
                    "Crew member goes overboard at night while alone on deck. "
                    "You discover them missing 5 minutes later. You were "
                    "running on autopilot at 8 knots. Water temperature is "
                    "45°F. No PLB or AIS beacon on the crew member. "
                    "Visibility is limited."
                ),
                "expected_keywords": [
                    "turn", "mark", "position", "GPS",
                    "Williamson", "search", "pattern",
                    "spotlight", "flares", "VHF",
                    "mayday", "hypothermia", "45",
                    "minutes", "survival", "time",
                ],
            },
            "hard": {
                "situation": (
                    "Two crew members swept overboard by a rogue wave while "
                    "working the aft deck. Vessel broached and lost power — "
                    "engine has stalled. One crew member has an AIS MOB beacon, "
                    "the other has nothing. Water temperature is 39°F. "
                    "10-foot seas, 30-knot winds, darkness. Remaining crew "
                    "of 2, one of whom is injured."
                ),
                "expected_keywords": [
                    "restart", "engine", "AIS", "MOB",
                    "beacon", "mayday", "VHF", "16",
                    "search", "pattern", "survival",
                    "time", "39", "minutes", "hypothermia",
                    "liferaft", "line", "throw",
                    "rope", "injured", "steerage",
                    "drift", "wind", "current",
                ],
            },
        },
    },
    "medical_emergency": {
        "difficulty_variants": {
            "easy": {
                "situation": (
                    "Crew member has a deep laceration on their forearm from "
                    "a knife. Bleeding is steady but not spurting. "
                    "You are 3 hours from port."
                ),
                "expected_keywords": [
                    "pressure", "direct", "elevate",
                    "clean", "dressing", "bandage",
                    "monitor", "shock", "signs",
                    "VHF", "medical", "advice",
                ],
            },
            "medium": {
                "situation": (
                    "Crew member is experiencing chest pain, shortness of "
                    "breath, and sweating. They are 55 years old, slightly "
                    "overweight. You are 6 hours from the nearest port. "
                    "Weather prevents helicopter evacuation for at least "
                    "2 hours."
                ),
                "expected_keywords": [
                    "heart", "cardiac", "aspirin",
                    "325", "mg", "VHF", "medical",
                    "Coast Guard", "evacuation", "position",
                    "oxygen", "if", "available", "monitor",
                    "pulse", "CPR", "ready",
                ],
            },
            "hard": {
                "situation": (
                    "Crew member was struck in the head by a swinging crab "
                    "pot and is now unconscious. Breathing is present but "
                    "irregular. Pupils are unequal. You are in the Bering Sea, "
                    "8 hours from a medical facility. Weather is too severe "
                    "for helicopter operations. Vessel is pitching violently, "
                    "making below-deck care difficult."
                ),
                "expected_keywords": [
                    "head", "injury", "traumatic", "brain",
                    "unconscious", "airway", "breathing",
                    "pulse", "stabilize", "cervical",
                    "spine", "do not", "move",
                    "oxygen", "VHF", "mayday",
                    "medical", "Coast Guard",
                    "communication", "evacuation", "weather",
                    "window", "monitor",
                ],
            },
        },
    },
    "vessel_power_loss": {
        "difficulty_variants": {
            "easy": {
                "situation": (
                    "Engine dies while entering harbor. You have steerage way "
                    "for another 30 seconds. Anchor is ready. Wind is light "
                    "and pushing you toward the breakwater."
                ),
                "expected_keywords": [
                    "anchor", "drop", "steerage",
                    "momentum", "breakwater", "clear",
                    "vessel", "VHF", "harbor",
                    "tow", "assistance", "drift",
                ],
            },
            "medium": {
                "situation": (
                    "Total electrical failure at night. Engine has stopped, "
                    "no navigation lights, no radio, no bilge pumps. You are "
                    "12 miles offshore in moderate traffic. Weather is "
                    "deteriorating — wind building from the southeast at "
                    "20 knots."
                ),
                "expected_keywords": [
                    "battery", "isolate", "fault",
                    "jump", "parallel", "backup",
                    "handheld", "VHF", "anchor",
                    "ballast", "drift", "position",
                    "visual", "distress", "signals",
                    "flares", "light", "sound",
                ],
            },
            "hard": {
                "situation": (
                    "Engine seizure at sea — catastrophic failure. Oil is "
                    "everywhere in the engine room. No propulsion. Electrical "
                    "is still working. You are 50 miles offshore, drifting "
                    "toward a lee shore in 35-knot winds. Tug response is "
                    "8 hours away. Crew of 5. Vessel is taking green water "
                    "over the bow."
                ),
                "expected_keywords": [
                    "mayday", "VHF", "16", "tow",
                    "position", "drift", "anchor",
                    "sea", "anchor", "drogue",
                    "trim", "ballast", "green water",
                    "hatches", "secure", "crew",
                    "PFD", "liferaft", "ready",
                    "abandon", "lines", "tug",
                    "ETA", "weather", "window",
                ],
            },
        },
    },
}

SYSTEM_PROMPT = (
    "You are Wesley, an emergency response officer on a commercial fishing vessel. "
    "You are given an emergency situation and must determine the correct response "
    "protocol. Prioritize life safety first, then vessel safety. Be specific about "
    "actions, sequence, and equipment. Keep your response under 300 words."
)


def generate_scenario(difficulty: str = "easy", seed: int | None = None) -> dict[str, Any]:
    """
    Generate an emergency response scenario.

    Args:
        difficulty: "easy", "medium", or "hard"
        seed: Optional random seed for reproducibility
    """
    rng = random.Random(seed)
    emergency_keys = list(EMERGENCIES.keys())
    rng.shuffle(emergency_keys)
    emergency_key = emergency_keys[0]
    emergency = EMERGENCIES[emergency_key]

    variant = emergency["difficulty_variants"].get(difficulty, emergency["difficulty_variants"]["easy"])

    prompt = (
        f"EMERGENCY RESPONSE TASK ({difficulty.upper()})\n\n"
        f"Situation: {variant['situation']}\n\n"
        f"Describe your response protocol. List actions in priority order. "
        f"Specify equipment used and crew assignments."
    )

    return {
        "task_type": "emergency_response",
        "prompt": prompt,
        "system_prompt": SYSTEM_PROMPT,
        "expected_keywords": variant["expected_keywords"],
        "correct_answer": "(evaluated on protocol correctness and completeness)",
        "difficulty": difficulty,
        "emergency_type": emergency_key,
    }
