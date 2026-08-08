"""
Evaluator — quality scoring for holodeck task responses.

Scores Wesley's responses on 4 dimensions:
  - accuracy: Does the answer contain the expected key facts?
  - specificity: Concrete details (numbers, technical terms, proper nouns)
  - reasoning: Logical reasoning chain (causal connectors, step-by-step)
  - completeness: All parts of the problem addressed

Each dimension is 0.0–1.0. The composite is a weighted average.

This extends the distillation_loop's score_response with task-specific
accuracy checking against expected answers.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class EvalResult:
    """Evaluation result for a single task attempt."""

    accuracy: float
    specificity: float
    reasoning: float
    completeness: float
    composite: float
    passed: bool
    matched_keywords: list[str] = field(default_factory=list)
    missed_keywords: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "accuracy": round(self.accuracy, 3),
            "specificity": round(self.specificity, 3),
            "reasoning": round(self.reasoning, 3),
            "completeness": round(self.completeness, 3),
            "composite": round(self.composite, 3),
            "passed": self.passed,
            "matched_keywords": self.matched_keywords,
            "missed_keywords": self.missed_keywords,
            "details": self.details,
        }


class Evaluator:
    """
    Evaluates task responses against expected answers.

    Usage:
        evaluator = Evaluator()
        result = evaluator.evaluate(
            response="The thermostat is stuck closed...",
            expected_keywords=["thermostat", "coolant", "overheating"],
            scenario={"prompt": "...", "difficulty": "easy"},
            task_type="engine_diagnosis",
            max_points=4,
        )
    """

    # Weights for composite score
    WEIGHTS = {
        "accuracy": 0.35,
        "specificity": 0.20,
        "reasoning": 0.25,
        "completeness": 0.20,
    }

    # Default pass threshold (composite score must meet or exceed)
    DEFAULT_THRESHOLD = 0.45

    def __init__(self, pass_threshold: float | None = None):
        self.pass_threshold = self.DEFAULT_THRESHOLD if pass_threshold is None else pass_threshold

    def evaluate(
        self,
        response: str,
        expected_keywords: list[str],
        scenario: dict[str, Any],
        task_type: str,
        max_points: int | None = None,
    ) -> EvalResult:
        """
        Evaluate a response against expected keywords and quality dimensions.

        Args:
            response: Wesley's response text
            expected_keywords: Key facts/terms that should appear in a good answer
            scenario: The scenario dict (contains prompt, difficulty, etc.)
            task_type: Which task type (engine_diagnosis, route_planning, etc.)
            max_points: Optional override for completeness max points

        Returns:
            EvalResult with scores and pass/fail
        """
        response_lower = response.lower()

        # ─── Accuracy ─────────────────────────────────────
        matched = []
        missed = []
        for kw in expected_keywords:
            if kw.lower() in response_lower:
                matched.append(kw)
            else:
                missed.append(kw)

        total_kw = len(expected_keywords) if expected_keywords else 1
        accuracy = len(matched) / total_kw

        # ─── Specificity ──────────────────────────────────
        specificity = self._score_specificity(response)

        # ─── Reasoning ────────────────────────────────────
        reasoning = self._score_reasoning(response)

        # ─── Completeness ─────────────────────────────────
        # `is None` check, not `or` — max_points=0 is a legitimate override
        # (same falsy-zero class as the pass_threshold=0.0 bug above).
        points = max_points if max_points is not None else len(expected_keywords)
        completeness = self._score_completeness(response, scenario, task_type, points)

        # ─── Composite ────────────────────────────────────
        composite = (
            accuracy * self.WEIGHTS["accuracy"]
            + specificity * self.WEIGHTS["specificity"]
            + reasoning * self.WEIGHTS["reasoning"]
            + completeness * self.WEIGHTS["completeness"]
        )

        passed = composite >= self.pass_threshold

        return EvalResult(
            accuracy=round(accuracy, 3),
            specificity=round(specificity, 3),
            reasoning=round(reasoning, 3),
            completeness=round(completeness, 3),
            composite=round(composite, 3),
            passed=passed,
            matched_keywords=matched,
            missed_keywords=missed,
            details={
                "task_type": task_type,
                "difficulty": scenario.get("difficulty", "unknown"),
                "total_keywords": total_kw,
                "matched_count": len(matched),
            },
        )

    def _score_specificity(self, text: str) -> float:
        """Score specificity: numbers, technical terms, proper nouns."""
        text_lower = text.lower()
        words = text_lower.split()
        if len(words) < 5:
            return 0.1

        # Numbers (measurements, temperatures, pressures, etc.)
        numbers = len(re.findall(r"\b\d+\.?\d*\s*(?:°|psi|rpm|kts?|mph|km|h|m|ft|lb|kg|mm|cm|in|amp|volt|kw|hp)?\b", text, re.IGNORECASE))

        # Technical terms relevant to maritime/engineering
        tech_terms = len(re.findall(
            r"\b(?:thermostat|coolant|impeller|alternator|injector|piston|"
            r"gasket|bearing|seal|hose|belt|filter|pump|valve|manifold|"
            r"current|tide|heading|bearing|waypoint|chart|nautical|"
            r"knot|speed|draft|clearance|channel|reef|shoal|"
            r"salmon|halibut|cod|pollock|herring|mackerel|tuna|"
            r"fiberglass|aluminum|steel|composite|polyurethane|epoxy|"
            r"starboard|port|bow|stern|aft|helm|"
            r"mayday|pan-pan|dewater|abandon|fire extinguisher|"
            r"life raft|PFD|EPIRB|flare|VHF|channel 16)\b",
            text_lower,
        ))

        sents = _sentences(text)
        denom = max(1, len(sents))
        score = min(1.0, (numbers + tech_terms) / denom)
        return score

    def _score_reasoning(self, text: str) -> float:
        """Score reasoning quality: causal connectors, step-by-step logic."""
        text_lower = text.lower()

        # Causal/logical connectors indicate reasoning chain
        connectors = len(re.findall(
            r"\b(?:because|since|due to|caused by|results? in|leads? to|"
            r"therefore|thus|so|which means|indicating|suggesting|"
            r"first|second|third|then|next|finally|step|"
            r"if\b|when\b|unless|otherwise|however|although)\b",
            text_lower,
        ))

        # Diagnostic reasoning patterns
        diagnostic = len(re.findall(
            r"\b(?:check|inspect|test|measure|verify|confirm|"
            r"look for|listen for|feel for|smell for|"
            r"diagnose|troubleshoot|rule out|eliminate)\b",
            text_lower,
        ))

        sents = _sentences(text)
        denom = max(1, len(sents))
        score = min(1.0, (connectors + diagnostic) / denom)
        return score

    def _score_completeness(
        self,
        text: str,
        scenario: dict[str, Any],
        task_type: str,
        max_points: int,
    ) -> float:
        """Score completeness: all parts of the problem addressed.

        max_points represents the number of distinct points a complete
        answer should cover. We combine this with structural and length
        signals to produce a holistic completeness score.
        """
        sents = _sentences(text)
        words = text.split()

        # Too short = incomplete
        if len(words) < 20:
            return 0.1
        if len(words) < 50:
            return 0.3

        # Check for structured response (lists, numbered points)
        numbered = len(re.findall(r"^\s*\d+[\.\)]\s", text, re.MULTILINE))
        bulleted = len(re.findall(r"^\s*[-•*]\s", text, re.MULTILINE))

        structure_bonus = min(0.3, (numbered + bulleted) * 0.1)

        # Base completeness from length and sentence count
        # Diminishing returns after ~10 sentences
        length_score = min(0.7, len(sents) / 10)

        # Keyword-coverage component: if the response addresses more of the
        # max_points expected points (approximated by keywords found in text),
        # boost the score. This rewards answers that cover more ground.
        response_lower = text.lower()
        expected_kws = scenario.get("expected_keywords", [])
        if expected_kws and max_points > 0:
            found = sum(1 for kw in expected_kws if kw.lower() in response_lower)
            coverage = min(1.0, found / max_points)
        else:
            coverage = 0.0

        # Blend: 50% length/structure, 50% keyword coverage
        blended = (length_score + structure_bonus) * 0.5 + coverage * 0.5
        score = min(1.0, blended)
        return score


def _sentences(text: str) -> list[str]:
    """Split text into sentences."""
    parts = re.split(r"[.!?]+", text)
    return [s.strip() for s in parts if s.strip()]
