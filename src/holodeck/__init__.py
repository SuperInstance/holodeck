"""
Holodeck — simulation training environment for Wesley.

The holodeck is where Wesley (Granite 3.1 2B via Ollama) practices real
maritime tasks in a safe sandbox. Each task type has a scenario generator,
an evaluator, and a difficulty curve. Successful attempts compile into .nail
reflexes; failures feed back into the distillation loop.

Architecture follows the exocortex roadmap Phase 3:
  - Scenario → Wesley attempt → Evaluation → Reflex or Failure log
  - Results feed into the distillation loop's weakness map
"""

__version__ = "0.1.0"

from holodeck.simulator import HolodeckSimulator, SimulationResult
from holodeck.evaluator import EvalResult, Evaluator
from holodeck.reporter import SessionReport

__all__ = [
    "HolodeckSimulator",
    "SimulationResult",
    "EvalResult",
    "Evaluator",
    "SessionReport",
]
