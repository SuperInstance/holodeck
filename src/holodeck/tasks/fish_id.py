"""
Fish Identification Task — given characteristics, identify the species.

Scenario generator produces fish descriptions for Alaska/Pacific species.
Evaluator checks for correct species identification and relevant detail.

Difficulty curve:
  easy:   Common species, distinctive features
  medium: Similar species, requires differentiation
  hard:   Unusual morphs, juveniles, or subtle differences
"""

from __future__ import annotations

import random
from typing import Any

# ─── Species Bank ──────────────────────────────────────────────

SPECIES = {
    "chinook_salmon": {
        "name": "Chinook Salmon (King)",
        "difficulty_variants": {
            "easy": {
                "description": (
                    "Large salmon, 30 pounds. Dark blue-green back with "
                    "silver sides. Black spots on both lobes of the tail. "
                    "Black mouth and gums."
                ),
                "expected_keywords": [
                    "chinook", "king", "salmon", "black mouth",
                    "spots", "tail", "both lobes",
                ],
            },
            "medium": {
                "description": (
                    "Salmon weighing 22 pounds caught near Seward in July. "
                    "Olive-brown back (ocean phase ending). Spots on tail "
                    "are large and irregular. Gums are dark. Anal fin has "
                    "15 rays."
                ),
                "expected_keywords": [
                    "chinook", "king", "dark gums", "anal fin",
                    "rays", "spots", "large",
                ],
            },
            "hard": {
                "description": (
                    "A 15-pound salmon caught in estuarine waters. Coloration "
                    "is transitioning — bronze-green back, no distinct spots "
                    "visible on the caudal peduncle. The fish has a shallow "
                    "body depth relative to length. Small, evenly-spaced spots "
                    "on the back only. Mouth lining is grayish-white."
                ),
                "expected_keywords": [
                    "chinook", "king", "transitioning", "caudal",
                    "mouth", "gray", "shallow", "ocean phase",
                    " differentiate",
                ],
            },
        },
    },
    "pacific_halibut": {
        "name": "Pacific Halibut",
        "difficulty_variants": {
            "easy": {
                "description": (
                    "Flatfish, both eyes on the right side of the head. "
                    "Dark brown mottled top side, white underside. "
                    "Diamond-shaped body. Weighs about 40 pounds."
                ),
                "expected_keywords": [
                    "halibut", "flatfish", "right-eyed", "mottled",
                    "white", "bottom", "diamond",
                ],
            },
            "medium": {
                "description": (
                    "Flatfish caught at 180 feet near Kodiak. 25 pounds. "
                    "Olive-green coloration on the eyed side with scattered "
                    "dark blotches. Lateral line has a high arch over the "
                    "pectoral fin. Tail is concave (crescent-shaped)."
                ),
                "expected_keywords": [
                    "halibut", "lateral line", "arch", "concave",
                    "tail", "blotches", "eyed side",
                ],
            },
            "hard": {
                "description": (
                    "A small flatfish (3 pounds) caught in shallow water. "
                    "Both eyes on the right side. Color is mottled sandy-brown. "
                    "Body shape is more elongated than typical. Lateral line "
                    "is nearly straight. Could be confused with a sand sole "
                    "or arrowtooth flounder at this size."
                ),
                "expected_keywords": [
                    "halibut", "small", "juvenile", "lateral line",
                    "straight", "arrowtooth", "sole", "differentiate",
                    "teeth", "lateral",
                ],
            },
        },
    },
    "pacific_cod": {
        "name": "Pacific Cod",
        "difficulty_variants": {
            "easy": {
                "description": (
                    "Long, slender fish with three dorsal fins and two anal "
                    "fins. Brownish-gray with darker mottling. Has a single "
                    "barbel (whisker) on its chin. Caught at 200 feet."
                ),
                "expected_keywords": [
                    "cod", "barbel", "chin", "dorsal", "anal",
                    "fins", "mottling",
                ],
            },
            "medium": {
                "description": (
                    "Gadid fish weighing 8 pounds. Three dorsal fins, two anal "
                    "fins. The barbel is short — about half the diameter of "
                    "the eye. Coloration ranges from gray to reddish-brown "
                    "depending on substrate. Lateral line is pale and visible."
                ),
                "expected_keywords": [
                    "cod", "gadid", "barbel", "eye", "dorsal",
                    "anal", "lateral line", "pale",
                ],
            },
            "hard": {
                "description": (
                    "A gadid caught at 350 feet. The fish has the characteristic "
                    "three dorsal and two anal fins, but the barbel is very "
                    "small and easily overlooked. Color is unusually dark — "
                    "nearly black on the dorsal surface. Could be confused "
                    "with walleye pollock at this depth."
                ),
                "expected_keywords": [
                    "cod", "pollock", "differentiate", "barbel",
                    "small", "dark", "dorsal", "anal", "depth",
                ],
            },
        },
    },
    "walleye_pollock": {
        "name": "Walleye Pollock",
        "difficulty_variants": {
            "easy": {
                "description": (
                    "Slender, silver fish with a speckled pattern. Three dorsal "
                    "fins, two anal fins. No chin barbel (unlike cod). Large eyes. "
                    "Forked tail. Caught midwater in the Bering Sea."
                ),
                "expected_keywords": [
                    "pollock", "no barbel", "large eyes", "dorsal",
                    "anal", "silver", "speckled",
                ],
            },
            "medium": {
                "description": (
                    "Gadid fish, 3 pounds. Olive-silver with golden sheen. "
                    "Three dorsals, two anals. Prominent lateral line that is "
                    "slightly arched. Eyes are notably large. No barbel or "
                    "a very tiny rudimentary one. Speckling is fine and uniform."
                ),
                "expected_keywords": [
                    "pollock", "eyes", "barbel", "tiny", "lateral line",
                    "speckling", "silver", "dorsal",
                ],
            },
            "hard": {
                "description": (
                    "A 2-pound gadid with silvery-gold coloration. The chin "
                    "barbel is present but minute — requires close inspection. "
                    "Eye diameter is large relative to body size. The first "
                    "dorsal fin is tall and pointed. Caught in the same haul "
                    "as Pacific cod of similar size."
                ),
                "expected_keywords": [
                    "pollock", "cod", "differentiate", "barbel",
                    "minute", "eye diameter", "dorsal", "tall",
                ],
            },
        },
    },
    "rockfish_species": {
        "name": "Rockfish (Species ID)",
        "difficulty_variants": {
            "easy": {
                "description": (
                    "Fish caught near a rocky reef at 120 feet. Bright orange-red "
                    "coloration. Spiny dorsal fin with 13 spines. Black mottling "
                    "on the sides. Large eyes. Distinctive light-colored lateral "
                    "line."
                ),
                "expected_keywords": [
                    "rockfish", "orange", "red", "spines", "dorsal",
                    "lateral line", "spiny", "reef",
                ],
            },
            "medium": {
                "description": (
                    "A Sebastes species caught at 250 feet. Dark red-brown body "
                    "with lighter ventral surface. Head spines are present but "
                    "weak. The lower jaw has a small symphyseal knob. "
                    "Caudal fin is slightly indented. No distinct stripes or bars."
                ),
                "expected_keywords": [
                    "rockfish", "Sebastes", "red", "head spines",
                    "symphyseal", "jaw", "caudal", "indented",
                ],
            },
            "hard": {
                "description": (
                    "A rockfish caught at 400 feet. Body is uniform dusky-pink "
                    "with no obvious markings. Fins have dark edges. The rakers "
                    "on the first gill arch number 28. Head is relatively narrow. "
                    "Anal fin has 7 rays. This fish could be one of several "
                    "similar Sebastes species."
                ),
                "expected_keywords": [
                    "rockfish", "Sebastes", "gill rakers", "anal rays",
                    "dusky", "pink", "species", "dark edges",
                    "narrow", "depth",
                ],
            },
        },
    },
}

SYSTEM_PROMPT = (
    "You are Wesley, a fisheries observer assistant on an Alaska fishing vessel. "
    "You are given a description of a fish and must identify the species. "
    "State your identification and explain which features led to your conclusion. "
    "Note any similar species and how you ruled them out. "
    "Keep your response under 250 words."
)


def generate_scenario(difficulty: str = "easy", seed: int | None = None) -> dict[str, Any]:
    """
    Generate a fish identification scenario.

    Args:
        difficulty: "easy", "medium", or "hard"
        seed: Optional random seed for reproducibility
    """
    rng = random.Random(seed)
    species_keys = list(SPECIES.keys())
    rng.shuffle(species_keys)
    species_key = species_keys[0]
    species = SPECIES[species_key]

    variant = species["difficulty_variants"].get(difficulty, species["difficulty_variants"]["easy"])

    prompt = (
        f"FISH IDENTIFICATION TASK ({difficulty.upper()})\n\n"
        f"Description: {variant['description']}\n\n"
        f"Identify the species. Explain your reasoning and note any "
        f"similar species you considered and ruled out."
    )

    # Merge species name into expected keywords as a strong signal
    keywords = list(variant["expected_keywords"])
    name_common = species["name"].split("(")[0].strip().lower()
    if name_common not in keywords:
        keywords.insert(0, name_common)

    return {
        "task_type": "fish_id",
        "prompt": prompt,
        "system_prompt": SYSTEM_PROMPT,
        "expected_keywords": keywords,
        "correct_answer": species["name"],
        "difficulty": difficulty,
        "species_name": species["name"],
    }
