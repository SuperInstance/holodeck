"""
Route Planning Task — given current/wind/obstacles, plot a course.

Scenario generator produces navigation challenges with varied conditions.
Evaluator checks for safe, efficient course selection.

Difficulty curve:
  easy:   Simple A-to-B with one obstacle
  medium: Multiple waypoints, current + wind
  hard:   Complex conditions, traffic, shallow draft constraints
"""

from __future__ import annotations

import random
from typing import Any

# ─── Scenario Bank ─────────────────────────────────────────────

SCENARIOS = {
    "simple_obstacle": {
        "difficulty_variants": {
            "easy": {
                "conditions": (
                    "You are at position 60°10'N, 149°25'W heading to "
                    "60°15'N, 149°30'W. There is a reef at 60°12'N, 149°28'W. "
                    "Current is negligible. Wind is 5 knots from the north."
                ),
                "ideal_route": "Depart heading northwest, arc west around the reef at 60°12'N, then approach destination from the east.",
                "expected_keywords": [
                    "around", "reef", "avoid", "heading", "northwest",
                    "west", "safe distance",
                ],
            },
            "medium": {
                "conditions": (
                    "Departing 59°45'N, 151°15'W for 59°52'N, 151°05'W. "
                    "A shoal extends from 59°48'N, 151°12'W to 59°50'N, 151°10'W. "
                    "Tidal current sets 090° at 1.5 knots. Wind 15 knots from "
                    "the southeast. Your vessel drafts 6 feet."
                ),
                "ideal_route": "Head north-northwest to clear the shoal's western edge, then adjust course east to compensate for the westerly current set. Approach destination from the southwest.",
                "expected_keywords": [
                    "shoal", "clear", "current", "set", "drift",
                    "compensate", "heading", "northwest", "draft",
                ],
            },
            "hard": {
                "conditions": (
                    "Transit from 60°20'N, 150°00'W to 60°35'N, 149°45'W. "
                    "Three hazards: reef at 60°25'N, 149°55'W; kelp bed at "
                    "60°28'N, 149°50'W; sandbar at 60°32'N, 149°48'W "
                    "(chart datum 4 feet at low water). Current sets 270° at "
                    "2 knots (spring tide). Wind 25 knots from the northeast. "
                    "Vessel draft: 5.5 feet. You have 3 hours of daylight left."
                ),
                "ideal_route": "Plot a wide eastern arc around all three hazards. Account for strong westerly current by steering well east of the rhumb line. The sandbar is impassable at this draft — give it at least 0.5 nm clearance. Consider waiting for slack current if transit time exceeds daylight.",
                "expected_keywords": [
                    "arc", "eastern", "clearance", "current", "westerly",
                    "rhumb line", "draft", "sandbar", "daylight",
                    "slack", "route", "waypoint",
                ],
            },
        },
    },
    "harbor_approach": {
        "difficulty_variants": {
            "easy": {
                "conditions": (
                    "Approaching Seward harbor from the east. Channel entrance "
                    "at 60°07'N, 149°26'W. Breakwater visible. Depth in channel "
                    "is 20 feet. Your draft is 5 feet. No traffic. Light wind."
                ),
                "ideal_route": "Approach the breakwater from the east, align with the channel markers, proceed at no-wake speed.",
                "expected_keywords": [
                    "channel", "breakwater", "markers", "no-wake",
                    "approach", "depth",
                ],
            },
            "medium": {
                "conditions": (
                    "Entering Seward harbor from Resurrection Bay. Visibility "
                    "1 mile in fog. Channel has a dog-leg at the second pair of "
                    "red/green markers. Tidal current 1 knot ebbing out of the "
                    "harbor. Draft 6 feet. Fishing vessel exiting the channel."
                ),
                "ideal_route": "Slow to no-wake, sound fog signals, monitor VHF 16 and 12. Follow range markers to the dog-leg, then turn to align with the inner channel. Hold starboard side of channel. Give way to outbound vessel (head-on situation, alter to starboard).",
                "expected_keywords": [
                    "fog", "slow", "no-wake", "sound signal", "VHF",
                    "range", "markers", "starboard", "give way",
                    "dog-leg", "current",
                ],
            },
            "hard": {
                "conditions": (
                    "Night approach to a unfamiliar harbor. Entrance channel is "
                    "150 feet wide with rock jetties on both sides. Cross-current "
                    "2 knots pushing toward the west jetty. Wind 20 knots from "
                    "the south. Swell running. Draft 6.5 feet. Charted depth at "
                    "the entrance is 8 feet (you are near low tide). Your radar "
                    "is working but the GPS chartplotter has lost fix."
                ),
                "ideal_route": "This is marginal. 8 feet of water with 6.5 foot draft in a 2-knot cross-current at night is dangerous. Consider standing off until flood tide adds water. If committed: use radar to range the jetties, steer a crab angle to compensate for current, transit at minimum steerage speed, have crew on the bow with spotlight.",
                "expected_keywords": [
                    "marginal", "dangerous", "tide", "draft", "clearance",
                    "radar", "crab angle", "compensate", "current",
                    "stand off", "minimum", "speed", "spotlight",
                ],
            },
        },
    },
    "crossing_recommended": {
        "difficulty_variants": {
            "easy": {
                "conditions": (
                    "You need to cross Cook Inlet from Homer to the west side. "
                    "Distance: 15 nautical miles. Current is 1 knot. "
                    "Wind is 10 knots. Your vessel cruises at 12 knots."
                ),
                "ideal_route": "Direct crossing is fine. Compensate slightly for current. ETA about 1 hour 20 minutes.",
                "expected_keywords": [
                    "crossing", "current", "compensate", "heading",
                    "ETA", "speed", "direct",
                ],
            },
            "medium": {
                "conditions": (
                    "Crossing Cook Inlet from Nikiski to Kalgin Island. "
                    "Distance 22nm. Tidal current sets north at 3 knots "
                    "(maximum). You must transit during the flood. West side "
                    "has extensive mudflats with 3-foot depths extending 2 miles "
                    "offshore. Your draft is 5 feet. Cruise speed 10 knots."
                ),
                "ideal_route": "Depart timed for slack water or early flood. Steer south of the rhumb line to compensate for northerly set. Approach Kalgin from the east, staying in water deeper than 6 feet. Do not cut the corner on approach — the mudflats extend well offshore.",
                "expected_keywords": [
                    "slack", "flood", "current", "compensate", "set",
                    "mudflats", "draft", "depth", "approach",
                    "corner", "offshore",
                ],
            },
            "hard": {
                "conditions": (
                    "Crossing northern Cook Inlet from the West Foreland to "
                    "Anchor Point. Distance 30nm. Tidal range is 25 feet. "
                    "Current can exceed 5 knots in the vicinity of Kalgin Island. "
                    "Sea state: 6-foot seas with wind against current. "
                    "You have a 32-foot vessel, draft 5 feet, cruise 8 knots. "
                    "Weather window is closing — front arriving in 6 hours."
                ),
                "ideal_route": "Marginal transit. The 5-knot current and 6-foot seas in a 32-foot vessel are at the edge of safe operations. Recommend delaying if possible. If committed: transit at max flood to ride the current north, then angle across. Avoid Kalgin Island shoals. Maintain sea room. If conditions deteriorate, divert to the nearest sheltered bay. Have mayday-ready equipment accessible.",
                "expected_keywords": [
                    "marginal", "dangerous", "current", "5 knots",
                    "delay", "flood", "sea room", "divert",
                    "shelter", "weather", "window", "safety",
                ],
            },
        },
    },
}

SYSTEM_PROMPT = (
    "You are Wesley, a navigation officer on a fishing vessel in Alaska waters. "
    "You are given a navigation scenario and must plot a safe, efficient course. "
    "Consider currents, wind, hazards, draft limitations, and traffic. "
    "Describe your planned route step by step. Keep your response under 300 words."
)


def generate_scenario(difficulty: str = "easy", seed: int | None = None) -> dict[str, Any]:
    """
    Generate a route planning scenario.

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
        f"ROUTE PLANNING TASK ({difficulty.upper()})\n\n"
        f"Conditions: {variant['conditions']}\n\n"
        f"Plot your course. Describe the route, explain your decisions, "
        f"and note any safety concerns."
    )

    return {
        "task_type": "route_planning",
        "prompt": prompt,
        "system_prompt": SYSTEM_PROMPT,
        "expected_keywords": variant["expected_keywords"],
        "correct_answer": variant["ideal_route"],
        "difficulty": difficulty,
        "scenario_name": scenario_key,
    }
