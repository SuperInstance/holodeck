"""
Holodeck task modules.

Each module provides:
  - generate_scenario(difficulty, seed) -> dict
  - SYSTEM_PROMPT
"""

from holodeck.tasks import (
    engine_diagnosis,
    emergency_response,
    fish_id,
    material_selection,
    radio_communication,
    route_planning,
)

# Registry: task_type -> module
TASK_REGISTRY = {
    "engine_diagnosis": engine_diagnosis,
    "route_planning": route_planning,
    "fish_id": fish_id,
    "material_selection": material_selection,
    "emergency_response": emergency_response,
    "radio_communication": radio_communication,
}

# Display names
TASK_NAMES = {
    "engine_diagnosis": "Engine Diagnosis",
    "route_planning": "Route Planning",
    "fish_id": "Fish Identification",
    "material_selection": "Material Selection",
    "emergency_response": "Emergency Response",
    "radio_communication": "Radio Communication",
}

# Difficulty levels in order
DIFFICULTIES = ["easy", "medium", "hard"]

__all__ = [
    "TASK_REGISTRY",
    "TASK_NAMES",
    "DIFFICULTIES",
    "engine_diagnosis",
    "route_planning",
    "fish_id",
    "material_selection",
    "emergency_response",
    "radio_communication",
]
