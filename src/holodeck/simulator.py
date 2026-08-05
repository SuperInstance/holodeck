"""
Holodeck Simulator — the main training loop.

Presents Wesley (Granite via Ollama) with maritime tasks, evaluates
responses, compiles successes into .nail reflexes, and logs failures
for the distillation loop to address.

Usage:
    python -m holodeck.simulator --tasks 10
    python -m holodeck.simulator --type engine_diagnosis --tasks 5
    python -m holodeck.simulator --difficulty hard --tasks 5
    python -m holodeck.simulator --dry-run --tasks 10
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from holodeck.evaluator import EvalResult, Evaluator
from holodeck.tasks import DIFFICULTIES, TASK_NAMES, TASK_REGISTRY

# ─── Paths ─────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = Path(os.environ.get("HOLODECK_OUTPUT", REPO_ROOT / "output"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

REFLEX_DIR = OUTPUT_DIR / "reflexes"
FAILURE_DIR = OUTPUT_DIR / "failures"
SESSION_DIR = OUTPUT_DIR / "sessions"
WEAKNESS_MAP_PATH = OUTPUT_DIR / "weakness_map.json"

for d in [REFLEX_DIR, FAILURE_DIR, SESSION_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ─── Ollama Configuration ──────────────────────────────────────

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/chat")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "granite3.1-dense:2b")
OLLAMA_BIN = os.environ.get("OLLAMA_BIN", "/home/eileen/.local/bin/ollama")


# ─── Data Structures ───────────────────────────────────────────


@dataclass
class SimulationResult:
    """Result of a single simulation attempt."""

    task_type: str
    difficulty: str
    scenario: dict[str, Any]
    response: str
    eval_result: EvalResult
    reflex_compiled: bool = False
    reflex_id: str = ""
    timestamp: str = ""
    response_time_ms: int = 0
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_type": self.task_type,
            "task_name": TASK_NAMES.get(self.task_type, self.task_type),
            "difficulty": self.difficulty,
            "response": self.response,
            "eval": self.eval_result.to_dict(),
            "reflex_compiled": self.reflex_compiled,
            "reflex_id": self.reflex_id,
            "timestamp": self.timestamp,
            "response_time_ms": self.response_time_ms,
            "error": self.error,
            "scenario_detail": {
                "difficulty": self.difficulty,
                "matched_keywords": self.eval_result.matched_keywords,
                "missed_keywords": self.eval_result.missed_keywords,
            },
        }


# ─── Ollama Interface ──────────────────────────────────────────


def call_ollama(system_prompt: str, user_prompt: str, timeout: int = 60) -> tuple[str, int]:
    """
    Call Ollama API and return (response_text, time_ms).

    Falls back to CLI if API is unavailable.
    """
    start = time.time()

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "options": {"temperature": 0.5, "top_p": 0.9},
    }

    try:
        import urllib.request

        req = urllib.request.Request(
            OLLAMA_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout + 15) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            msg = result.get("message", {})
            text = msg.get("content", "") if isinstance(msg, dict) else str(msg)
            elapsed = int((time.time() - start) * 1000)
            return text, elapsed
    except Exception as api_err:
        # Fallback to CLI
        try:
            cli_prompt = f"{system_prompt}\n\n{user_prompt}"
            result = subprocess.run(
                [OLLAMA_BIN, "run", OLLAMA_MODEL, cli_prompt],
                capture_output=True,
                text=True,
                timeout=timeout + 30,
            )
            text = result.stdout.strip() if result.returncode == 0 else f"(CLI error: {result.stderr.strip()})"
            elapsed = int((time.time() - start) * 1000)
            return text, elapsed
        except Exception as cli_err:
            elapsed = int((time.time() - start) * 1000)
            return f"(Error: API={api_err}, CLI={cli_err})", elapsed


def mock_response(scenario: dict[str, Any]) -> str:
    """Generate a mock response for dry-run mode."""
    correct_answer = scenario.get("correct_answer", "")
    keywords = scenario.get("expected_keywords", [])
    # Include ~60% of keywords to simulate a mediocre response
    import random

    rng = random.Random(hash(scenario["prompt"]) % 2**32)
    included = rng.sample(keywords, max(1, len(keywords) * 3 // 5))
    return (
        f"Based on the symptoms described, I believe the issue is: {correct_answer[:150]}. "
        f"Key indicators include: {', '.join(included[:4])}. "
        f"I would recommend inspecting and addressing the {included[0] if included else 'system'} "
        f"component first, then proceeding with standard troubleshooting. "
        f"This is consistent with known patterns in marine engineering."
    )


# ─── Reflex Compilation ────────────────────────────────────────


def compile_reflex(
    task_type: str,
    scenario: dict[str, Any],
    response: str,
    eval_result: EvalResult,
) -> dict[str, Any]:
    """
    Compile a successful attempt into a .nail reflex.

    The reflex allows Wesley to reproduce the good behavior without
    needing to reason from scratch next time.
    """
    situation = f"task={task_type} difficulty={scenario.get('difficulty', 'unknown')}"

    raw = f"{task_type}|{scenario.get('difficulty', '')}|{eval_result.composite}|{time.time()}"
    nail_id = hashlib.sha256(raw.encode()).hexdigest()[:16]

    nail = {
        "id": nail_id,
        "domain": "holodeck",
        "task_type": task_type,
        "situation": situation,
        "scenario_detail": {
            "difficulty": scenario.get("difficulty"),
            "problem_name": scenario.get("problem_name", scenario.get("scenario_name", "")),
        },
        "response_excerpt": response[:500],
        "action": f"execute_{task_type}_protocol",
        "outcome": "success",
        "outcome_quality": eval_result.composite,
        "confidence": min(0.9, eval_result.composite + 0.1),
        "matched_keywords": eval_result.matched_keywords,
        "missed_keywords": eval_result.missed_keywords,
        "scores": {
            "accuracy": eval_result.accuracy,
            "specificity": eval_result.specificity,
            "reasoning": eval_result.reasoning,
            "completeness": eval_result.completeness,
        },
        "metadata": {
            "source": "holodeck",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }

    nail_path = REFLEX_DIR / f"{nail_id}.nail.json"
    nail_path.write_text(json.dumps(nail, indent=2, ensure_ascii=False), encoding="utf-8")

    return {"compiled": True, "nail_id": nail_id, "path": str(nail_path)}


def log_failure(
    task_type: str,
    scenario: dict[str, Any],
    response: str,
    eval_result: EvalResult,
) -> None:
    """Log a failed attempt for the distillation loop to address."""
    failure = {
        "task_type": task_type,
        "difficulty": scenario.get("difficulty"),
        "prompt": scenario["prompt"],
        "response": response,
        "scores": eval_result.to_dict(),
        "missed_keywords": eval_result.missed_keywords,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    failure_path = FAILURE_DIR / f"{task_type}_failures.jsonl"
    with open(failure_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(failure, ensure_ascii=False) + "\n")


# ─── Weakness Map ──────────────────────────────────────────────


def update_weakness_map(results: list[SimulationResult]) -> dict[str, Any]:
    """
    Update the weakness map with results from this session.

    The weakness map tracks which task types Wesley handles well vs poorly,
    so the distillation loop can target gaps.
    """
    if WEAKNESS_MAP_PATH.exists():
        try:
            weakness_map = json.loads(WEAKNESS_MAP_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            weakness_map = {}
    else:
        weakness_map = {}

    for result in results:
        key = result.task_type
        if key not in weakness_map:
            weakness_map[key] = {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "pass_rate": 0.0,
                "avg_composite": 0.0,
                "avg_accuracy": 0.0,
                "by_difficulty": {},
            }

        entry = weakness_map[key]
        entry["total"] += 1
        if result.eval_result.passed:
            entry["passed"] += 1
        else:
            entry["failed"] += 1

        entry["pass_rate"] = round(entry["passed"] / entry["total"], 3)
        # Running average
        n = entry["total"]
        entry["avg_composite"] = round(
            (entry["avg_composite"] * (n - 1) + result.eval_result.composite) / n, 3
        )
        entry["avg_accuracy"] = round(
            (entry["avg_accuracy"] * (n - 1) + result.eval_result.accuracy) / n, 3
        )

        # By difficulty
        diff = result.difficulty
        if diff not in entry["by_difficulty"]:
            entry["by_difficulty"][diff] = {"total": 0, "passed": 0, "pass_rate": 0.0}
        entry["by_difficulty"][diff]["total"] += 1
        if result.eval_result.passed:
            entry["by_difficulty"][diff]["passed"] += 1
        d = entry["by_difficulty"][diff]
        d["pass_rate"] = round(d["passed"] / d["total"], 3)

    WEAKNESS_MAP_PATH.write_text(json.dumps(weakness_map, indent=2, ensure_ascii=False), encoding="utf-8")
    return weakness_map


# ─── Main Simulator ────────────────────────────────────────────


class HolodeckSimulator:
    """
    The main holodeck simulator.

    Usage:
        sim = HolodeckSimulator()
        results = sim.run_session(tasks=10)
        report = sim.get_report(results)
    """

    def __init__(
        self,
        evaluator: Evaluator | None = None,
        pass_threshold: float | None = None,
        dry_run: bool = False,
    ):
        self.evaluator = evaluator or Evaluator(pass_threshold)
        self.dry_run = dry_run
        self.session_results: list[SimulationResult] = []

    def run_single(
        self,
        task_type: str,
        difficulty: str = "easy",
        seed: int | None = None,
    ) -> SimulationResult:
        """Run a single simulation attempt."""
        module = TASK_REGISTRY[task_type]
        scenario = module.generate_scenario(difficulty=difficulty, seed=seed)

        timestamp = datetime.now(timezone.utc).isoformat()

        if self.dry_run:
            response = mock_response(scenario)
            response_time_ms = 100
        else:
            response, response_time_ms = call_ollama(
                system_prompt=scenario["system_prompt"],
                user_prompt=scenario["prompt"],
            )

        eval_result = self.evaluator.evaluate(
            response=response,
            expected_keywords=scenario["expected_keywords"],
            scenario=scenario,
            task_type=task_type,
        )

        reflex_compiled = False
        reflex_id = ""
        if eval_result.passed:
            reflex = compile_reflex(task_type, scenario, response, eval_result)
            reflex_compiled = reflex["compiled"]
            reflex_id = reflex["nail_id"]
        else:
            log_failure(task_type, scenario, response, eval_result)

        return SimulationResult(
            task_type=task_type,
            difficulty=difficulty,
            scenario=scenario,
            response=response,
            eval_result=eval_result,
            reflex_compiled=reflex_compiled,
            reflex_id=reflex_id,
            timestamp=timestamp,
            response_time_ms=response_time_ms,
        )

    def run_session(
        self,
        tasks: int = 10,
        task_type: str | None = None,
        difficulty: str | None = None,
        seed_offset: int = 0,
    ) -> list[SimulationResult]:
        """
        Run a training session with N tasks.

        Tasks are distributed across task types and difficulty levels
        unless specific ones are provided.
        """
        results: list[SimulationResult] = []

        all_task_types = list(TASK_REGISTRY.keys())

        for i in range(tasks):
            # Determine task type
            tt = task_type or all_task_types[i % len(all_task_types)]

            # Determine difficulty — escalate based on progress
            if difficulty:
                diff = difficulty
            else:
                # Rotate through difficulties, weighted toward easier early
                progress = i / max(1, tasks - 1) if tasks > 1 else 0
                if progress < 0.33:
                    diff = DIFFICULTIES[0]  # easy
                elif progress < 0.66:
                    diff = DIFFICULTIES[1]  # medium
                else:
                    diff = DIFFICULTIES[2]  # hard

            seed = seed_offset + i * 1009  # Prime-spaced seeds
            result = self.run_single(tt, diff, seed)
            results.append(result)

            # Print progress
            status = "✅ PASS" if result.eval_result.passed else "❌ FAIL"
            composite = result.eval_result.composite
            print(
                f"  [{i+1:2d}/{tasks}] {TASK_NAMES.get(tt, tt):25s} "
                f"({diff:6s}) {status}  score={composite:.3f}  "
                f"{'→ reflex' if result.reflex_compiled else '→ logged'}",
                flush=True,
            )

        self.session_results = results
        update_weakness_map(results)
        return results

    def save_session(self, results: list[SimulationResult] | None = None) -> Path:
        """Save session results to a JSONL file."""
        # `is None` check, not `or` — an explicit results=[] must stay empty,
        # not silently fall back to self.session_results (falsy-zero class bug).
        results = results if results is not None else self.session_results
        if not results:
            return SESSION_DIR / "empty.jsonl"

        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        path = SESSION_DIR / f"session_{ts}.jsonl"
        with open(path, "w", encoding="utf-8") as f:
            for r in results:
                f.write(json.dumps(r.to_dict(), ensure_ascii=False) + "\n")
        return path


# ─── CLI ───────────────────────────────────────────────────────


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Holodeck — simulation training for Wesley",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  holodeck --tasks 10              # Run 10 tasks across all types\n"
            "  holodeck --type engine_diagnosis  # Only engine diagnosis\n"
            "  holodeck --difficulty hard         # Hard difficulty only\n"
            "  holodeck --dry-run --tasks 10     # No Ollama, for testing\n"
        ),
    )
    parser.add_argument(
        "--tasks", "-n", type=int, default=10,
        help="Number of tasks to run (default: 10)",
    )
    parser.add_argument(
        "--type", "-t",
        choices=list(TASK_REGISTRY.keys()),
        default=None,
        help="Specific task type (default: rotate through all)",
    )
    parser.add_argument(
        "--difficulty", "-d",
        choices=DIFFICULTIES,
        default=None,
        help="Difficulty level (default: auto-escalate)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Mock mode — no Ollama calls, for testing",
    )
    parser.add_argument(
        "--threshold", type=float, default=None,
        help="Pass threshold override (default: 0.45)",
    )
    parser.add_argument(
        "--seed", type=int, default=None,
        help="Random seed for reproducibility",
    )
    parser.add_argument(
        "--report", action="store_true",
        help="Print detailed session report",
    )

    args = parser.parse_args()

    print("╔══════════════════════════════════════════════╗", flush=True)
    print("║          HOLODECK TRAINING SIMULATOR         ║", flush=True)
    print("╚══════════════════════════════════════════════╝", flush=True)
    print(flush=True)
    print(f"  Model:     {OLLAMA_MODEL}", flush=True)
    print(f"  Tasks:     {args.tasks}", flush=True)
    print(f"  Type:      {args.type or 'all (rotating)'}", flush=True)
    print(f"  Difficulty: {args.difficulty or 'auto-escalate'}", flush=True)
    print(f"  Mode:      {'DRY RUN' if args.dry_run else 'LIVE (Ollama)'}", flush=True)
    print(flush=True)

    sim = HolodeckSimulator(
        pass_threshold=args.threshold,
        dry_run=args.dry_run,
    )

    results = sim.run_session(
        tasks=args.tasks,
        task_type=args.type,
        difficulty=args.difficulty,
        seed_offset=args.seed or 0,
    )

    # Save session
    session_path = sim.save_session(results)

    # Summary
    passed = sum(1 for r in results if r.eval_result.passed)
    failed = len(results) - passed
    avg_score = sum(r.eval_result.composite for r in results) / len(results) if results else 0
    reflexes = sum(1 for r in results if r.reflex_compiled)
    avg_time = sum(r.response_time_ms for r in results) / len(results) if results else 0

    print(flush=True)
    print("─" * 50, flush=True)
    print(f"  RESULTS: {passed} passed, {failed} failed", flush=True)
    print(f"  Avg score: {avg_score:.3f}", flush=True)
    print(f"  Reflexes compiled: {reflexes}", flush=True)
    print(f"  Avg response time: {avg_time:.0f}ms", flush=True)
    print(f"  Session saved: {session_path}", flush=True)
    print(f"  Weakness map: {WEAKNESS_MAP_PATH}", flush=True)
    print("─" * 50, flush=True)

    if args.report:
        from holodeck.reporter import SessionReport

        report = SessionReport(results)
        print(flush=True)
        print(report.render_text(), flush=True)

    # Exit code: 0 if any passed, 1 if all failed
    sys.exit(0 if passed > 0 else 1)


if __name__ == "__main__":
    main()
