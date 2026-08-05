"""
Radio Communication Task — VHF protocol, distress calls, channel etiquette.

Scenario generator produces maritime radio communication scenarios.
Tests Wesley's knowledge of VHF procedures, ITU phonetics, channel
assignments, and standard message formatting.

Difficulty curve:
  easy:   Routine communication — bridge-to-bridge, marina, weather check
  medium: Urgency/safety messages — Pan-Pan, Sécurité, broken communication
  hard:   Distress scenarios — Mayday, relay, silence, complex multi-vessel
"""

from __future__ import annotations

import random
from typing import Any

# ─── Scenario Bank ─────────────────────────────────────────────

SCENARIOS = {
    "routine_bridge_to_bridge": {
        "difficulty_variants": {
            "easy": {
                "situation": (
                    "You are the FV Aurora, a 42-foot fishing vessel, "
                    "approaching the entrance to Seldovia Bay. There is "
                    "another vessel exiting the channel. You need to "
                    "arrange a port-to-port passing."
                ),
                "expected_keywords": [
                    "channel", "13", "or", "16",
                    "FV Aurora", "calling",
                    "inbound", "outbound",
                    "port", "to", "port",
                    "one", "whistle", "agree",
                ],
            },
            "medium": {
                "situation": (
                    "You are the FV Aurora approaching Narrow Strait in "
                    "reduced visibility (fog). Vessel traffic is heavy. "
                    "You need to broadcast a security message and coordinate "
                    "movements with two other fishing vessels transiting "
                    "the same area."
                ),
                "expected_keywords": [
                    "securite", "securite", "securite",
                    "channel", "16", "then", "13",
                    "position", "course", "speed",
                    "slow", "fog", "restricted",
                    "visibility", "radar", "agreed",
                    "passing", "arrangement",
                ],
            },
            "hard": {
                "situation": (
                    "You are the FV Aurora in international waters. A "
                    "foreign-flagged vessel is approaching your fishing "
                    "gear. You need to communicate on VHF but are unsure "
                    "if they monitor channel 16. There is a language "
                    "barrier. You also need to report your catch to your "
                    "company office via a marine operator connection."
                ),
                "expected_keywords": [
                    "channel", "16", "calling",
                    "international", "ITU", "phonetic",
                    "alphabet", "marine", "operator",
                    "channel", "26", "or", "27",
                    "company", "call", "sign",
                    "language", "barrier", "standard",
                    "maritime", "phrases", "slow",
                    "clear",
                ],
            },
        },
    },
    "distress_mayday": {
        "difficulty_variants": {
            "easy": {
                "situation": (
                    "Your vessel is taking on water rapidly through a "
                    "failed through-hull fitting. You are 5 miles northwest "
                    "of Homer Spit. You have 4 crew aboard. The vessel is "
                    "the FV Aurora, callsign WDF-4421. You need to broadcast "
                    "a Mayday."
                ),
                "expected_keywords": [
                    "mayday", "mayday", "mayday",
                    "any", "station", "FV Aurora",
                    "WDF", "4421", "sinking",
                    "position", "5", "miles", "northwest",
                    "Homer", "4", "crew",
                    "immediate", "assistance",
                ],
            },
            "medium": {
                "situation": (
                    "You witness a vessel capsize approximately 2 miles to "
                    "your east. You cannot reach them on VHF. You are the "
                    "FV Aurora, callsign WDF-4421, positioned 12 miles "
                    "southwest of Kodiak. You need to issue a Mayday Relay."
                ),
                "expected_keywords": [
                    "mayday", "relay", "mayday", "relay",
                    "FV Aurora", "WDF", "4421",
                    "intercepted", "or", "visual",
                    "vessel", "capsized", "2", "miles",
                    "east", "position", "12",
                    "miles", "southwest", "Kodiak",
                    "persons", "in", "water",
                ],
            },
            "hard": {
                "situation": (
                    "You are the FV Aurora. You have broadcast a Mayday "
                    "for an engine room fire. The Coast Guard has acknowledged "
                    "and is responding. A nearby vessel, the MV Stellar, is "
                    "also responding but is cluttering channel 16 with "
                    "unnecessary transmissions. Another vessel is trying "
                    "to make a routine call on 16. Explain how you manage "
                    "radio discipline during the ongoing distress incident."
                ),
                "expected_keywords": [
                    "silence", "mayday", "seelonce",
                    "feenee", "or", "prudonce",
                    "channel", "16", "working",
                    "frequency", "Coast", "Guard",
                    "assign", "MV", "Stellar",
                    "stand", "by", "routine",
                    "traffic", "defer", "distress",
                    "priority", "controlling",
                    "station",
                ],
            },
        },
    },
    "pan_pan_medical": {
        "difficulty_variants": {
            "easy": {
                "situation": (
                    "A crew member has a suspected broken leg. You are "
                    "4 hours from port, motoring at 8 knots. Weather is "
                    "fair. You are the FV Aurora, callsign WDF-4421, "
                    "20 miles east of Homer. You need to request medical "
                    "advice."
                ),
                "expected_keywords": [
                    "pan", "pan", "pan",
                    "medical", "advice", "or",
                    "Coast", "Guard",
                    "FV Aurora", "WDF", "4421",
                    "position", "broken", "leg",
                    "channel", "22", "alpha",
                    "or", "working", "frequency",
                ],
            },
            "medium": {
                "situation": (
                    "A crew member is showing signs of a heart attack. "
                    "You need urgent medical evacuation. You are 35 miles "
                    "offshore, the FV Aurora, callsign WDF-4421. Weather "
                    "is deteriorating — winds 25 knots, seas 8 feet. "
                    "Helicopter evacuation may be needed."
                ),
                "expected_keywords": [
                    "pan", "pan", "pan",
                    "FV Aurora", "WDF", "4421",
                    "medical", "emergency", "heart",
                    "position", "35", "miles",
                    "offshore", "evacuation",
                    "helicopter", "weather",
                    "25", "knots", "8", "feet",
                    "hoist", "briefing", "clear",
                    "deck", "ready",
                ],
            },
            "hard": {
                "situation": (
                    "A crew member has been struck by a crab pot and is "
                    "unconscious with a severe head injury. You are in the "
                    "Bering Sea, 60 miles north of Unalaska. You are the "
                    "FV Aurora, callsign WDF-4421. Weather is severe — "
                    "gale force winds, 15-foot seas, freezing spray. "
                    "Helicopter range is marginal. A nearby factory "
                    "trawler has a medic. You need to coordinate medical "
                    "evacuation across multiple assets and frequencies."
                ),
                "expected_keywords": [
                    "pan", "pan", "pan",
                    "or", "mayday", "if",
                    "life", "threatening",
                    "FV Aurora", "WDF", "4421",
                    "position", "60", "miles",
                    "Unalaska", "unconscious",
                    "head", "injury", "helicopter",
                    "range", "marginal",
                    "factory", "trawler", "medic",
                    "rendezvous", "working",
                    "channel", "transfer",
                    "hoist", "gale", "freezing",
                    "spray", "deck", "crew",
                    "PFD", "survival",
                ],
            },
        },
    },
    "digital_selective_calling": {
        "difficulty_variants": {
            "easy": {
                "situation": (
                    "Your DSC radio is sending out a routine position "
                    "request to your buddy boat, the FV Nordic Star. "
                    "Explain the DSC procedure for a routine individual "
                    "call and what happens on the receiving end."
                ),
                "expected_keywords": [
                    "DSC", "individual", "call",
                    "MMSI", "category", "routine",
                    "channel", "70", "working",
                    "channel", "acknowledge",
                    "automatic", "switch",
                ],
            },
            "medium": {
                "situation": (
                    "You need to send a DSC distress alert. Your vessel "
                    "is the FV Aurora, MMSI 338123456. You are sinking "
                    "20 miles southwest of Seward. Explain the full DSC "
                    "distress procedure including what happens after "
                    "the alert is sent."
                ),
                "expected_keywords": [
                    "DSC", "distress", "button",
                    "or", "menu", "distress",
                    "nature", "sinking", "or",
                    "flooding", "position",
                    "20", "miles", "Seward",
                    "MMSI", "338123456",
                    "channel", "70", "wait",
                    "acknowledgment", "follow",
                    "up", "voice", "mayday",
                    "channel", "16",
                ],
            },
            "hard": {
                "situation": (
                    "You received a DSC distress alert on channel 70 but "
                    "cannot raise the vessel on channel 16. There is no "
                    "GPS position in the alert — only an MMSI. You are "
                    "in an area with heavy traffic and multiple vessels "
                    "are responding. The Coast Guard has not yet "
                    "acknowledged. Walk through the complete DSC distress "
                    "relay procedure including voice relay."
                ),
                "expected_keywords": [
                    "DSC", "distress", "relay",
                    "channel", "70", "MMSI",
                    "no", "position", "voice",
                    "mayday", "relay", "channel",
                    "16", "Coast", "Guard",
                    "not", "acknowledged", "wait",
                    "two", "minutes", "retransmit",
                    "coordinates", "uncertain",
                    "traffic", "control", "silence",
                ],
            },
        },
    },
}

SYSTEM_PROMPT = (
    "You are Wesley, the radio communications officer on a commercial fishing vessel. "
    "You are given a marine radio scenario and must describe the correct VHF procedure. "
    "Use proper terminology: Mayday, Pan-Pan, Sécurité, ITU phonetic alphabet, "
    "channel numbers, and standard maritime phrases. Be precise about frequencies "
    "and protocols. Keep your response under 300 words."
)


def generate_scenario(difficulty: str = "easy", seed: int | None = None) -> dict[str, Any]:
    """
    Generate a radio communication scenario.

    Args:
        difficulty: "easy", "medium", or "hard"
        seed: Optional random seed for reproducibility
    """
    rng = random.Random(seed)
    scenario_keys = list(SCENARIOS.keys())
    rng.shuffle(scenario_keys)
    scenario_key = scenario_keys[0]
    scenario = SCENARIOS[scenario_key]

    variant = scenario["difficulty_variants"].get(
        difficulty, scenario["difficulty_variants"]["easy"]
    )

    prompt = (
        f"RADIO COMMUNICATION TASK ({difficulty.upper()})\n\n"
        f"Situation: {variant['situation']}\n\n"
        f"Describe the correct radio procedure. Include exact wording where "
        f"appropriate. Specify channels and frequencies. Use the ITU phonetic "
        f"alphabet for callsigns."
    )

    return {
        "task_type": "radio_communication",
        "prompt": prompt,
        "system_prompt": SYSTEM_PROMPT,
        "expected_keywords": variant["expected_keywords"],
        "correct_answer": "(evaluated on procedure correctness and terminology)",
        "difficulty": difficulty,
        "scenario_type": scenario_key,
    }
