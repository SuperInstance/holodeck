"""
Reporter — training session summary and analysis.

Generates human-readable reports from holodeck training sessions.
Also provides machine-readable summaries for integration with the
distillation loop and the broader exocortex.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from holodeck.simulator import SimulationResult
from holodeck.tasks import TASK_NAMES


@dataclass
class SessionReport:
    """Analyzes and renders a training session report."""

    results: list[SimulationResult]

    def __post_init__(self):
        self._analyze()

    def _analyze(self):
        """Compute all statistics."""
        self.total = len(self.results)
        self.passed = sum(1 for r in self.results if r.eval_result.passed)
        self.failed = self.total - self.passed
        self.pass_rate = self.passed / self.total if self.total > 0 else 0
        self.avg_score = (
            sum(r.eval_result.composite for r in self.results) / self.total
            if self.total > 0
            else 0
        )
        self.reflexes_compiled = sum(1 for r in self.results if r.reflex_compiled)
        self.avg_response_time = (
            sum(r.response_time_ms for r in self.results) / self.total
            if self.total > 0
            else 0
        )

        # Per-task-type breakdown
        self.by_type: dict[str, dict[str, Any]] = defaultdict(lambda: {
            "total": 0, "passed": 0, "failed": 0,
            "scores": [], "avg_composite": 0.0, "avg_accuracy": 0.0,
        })
        for r in self.results:
            entry = self.by_type[r.task_type]
            entry["total"] += 1
            if r.eval_result.passed:
                entry["passed"] += 1
            else:
                entry["failed"] += 1
            entry["scores"].append(r.eval_result.composite)

        for tt, entry in self.by_type.items():
            scores = entry.pop("scores")
            entry["avg_composite"] = round(sum(scores) / len(scores), 3) if scores else 0
            entry["avg_accuracy"] = round(
                sum(
                    r.eval_result.accuracy for r in self.results
                    if r.task_type == tt
                ) / max(1, sum(1 for r in self.results if r.task_type == tt)),
                3,
            )
            entry["pass_rate"] = round(entry["passed"] / entry["total"], 3) if entry["total"] else 0

        # Per-difficulty breakdown
        self.by_difficulty: dict[str, dict[str, Any]] = defaultdict(lambda: {
            "total": 0, "passed": 0, "failed": 0, "avg_score": 0.0,
        })
        for r in self.results:
            entry = self.by_difficulty[r.difficulty]
            entry["total"] += 1
            if r.eval_result.passed:
                entry["passed"] += 1
            else:
                entry["failed"] += 1
        for diff, entry in self.by_difficulty.items():
            scores = [r.eval_result.composite for r in self.results if r.difficulty == diff]
            entry["avg_score"] = round(sum(scores) / len(scores), 3) if scores else 0
            entry["pass_rate"] = round(entry["passed"] / entry["total"], 3) if entry["total"] else 0

        # Identify weakest task type
        self.weakest_type = min(
            self.by_type.items(),
            key=lambda x: x[1]["avg_composite"],
            default=(None, {}),
        )
        self.strongest_type = max(
            self.by_type.items(),
            key=lambda x: x[1]["avg_composite"],
            default=(None, {}),
        )

        # Collect all missed keywords for weakness analysis
        all_missed: dict[str, int] = defaultdict(int)
        for r in self.results:
            for kw in r.eval_result.missed_keywords:
                all_missed[kw] += 1
        self.missed_keywords = dict(
            sorted(all_missed.items(), key=lambda x: -x[1])
        )

    def render_text(self) -> str:
        """Render the report as formatted text for terminal output."""
        lines = []
        lines.append("╔══════════════════════════════════════════════════╗")
        lines.append("║          HOLODECK SESSION REPORT                ║")
        lines.append("╚══════════════════════════════════════════════════╝")
        lines.append("")
        lines.append("OVERALL")
        lines.append(f"  Tasks run:      {self.total}")
        lines.append(f"  Passed:         {self.passed} ({self.pass_rate:.1%})")
        lines.append(f"  Failed:         {self.failed}")
        lines.append(f"  Avg score:      {self.avg_score:.3f}")
        lines.append(f"  Reflexes:       {self.reflexes_compiled}")
        lines.append(f"  Avg resp time:  {self.avg_response_time:.0f}ms")
        lines.append("")

        lines.append("BY TASK TYPE")
        for tt, stats in sorted(self.by_type.items()):
            name = TASK_NAMES.get(tt, tt)
            lines.append(
                f"  {name:25s}  "
                f"{stats['passed']}/{stats['total']} passed  "
                f"avg={stats['avg_composite']:.3f}  "
                f"acc={stats['avg_accuracy']:.3f}"
            )
        lines.append("")

        lines.append("BY DIFFICULTY")
        for diff in ["easy", "medium", "hard"]:
            if diff in self.by_difficulty:
                stats = self.by_difficulty[diff]
                lines.append(
                    f"  {diff:8s}  "
                    f"{stats['passed']}/{stats['total']} passed  "
                    f"avg={stats['avg_score']:.3f}"
                )
        lines.append("")

        if self.weakest_type[0]:
            w_name = TASK_NAMES.get(self.weakest_type[0], self.weakest_type[0])
            w_score = self.weakest_type[1]["avg_composite"]
            s_name = TASK_NAMES.get(self.strongest_type[0], self.strongest_type[0])
            s_score = self.strongest_type[1]["avg_composite"]
            lines.append("ASSESSMENT")
            lines.append(f"  Strongest:  {s_name} ({s_score:.3f})")
            lines.append(f"  Weakest:    {w_name} ({w_score:.3f})")
            lines.append("")

        if self.missed_keywords:
            lines.append("TOP MISSED KEYWORDS (distillation targets)")
            for kw, count in list(self.missed_keywords.items())[:10]:
                lines.append(f"  {kw:30s}  missed {count}x")
            lines.append("")

        lines.append("RECOMMENDATION")
        if self.pass_rate >= 0.7:
            lines.append("  Wesley is performing well. Consider increasing difficulty.")
        elif self.pass_rate >= 0.4:
            lines.append("  Wesley shows partial competence. Target weak areas in distillation.")
        else:
            lines.append("  Wesley is struggling. Recommend focused distillation before next sim run.")
        if self.missed_keywords:
            lines.append(
                f"  Feed {len(self.missed_keywords)} missed keywords into the distillation loop."
            )

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Machine-readable report for integration."""
        return {
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "pass_rate": round(self.pass_rate, 3),
            "avg_score": round(self.avg_score, 3),
            "reflexes_compiled": self.reflexes_compiled,
            "avg_response_time_ms": round(self.avg_response_time, 0),
            "by_type": dict(self.by_type),
            "by_difficulty": dict(self.by_difficulty),
            "weakest_type": self.weakest_type[0],
            "strongest_type": self.strongest_type[0],
            "missed_keywords": self.missed_keywords,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    def save(self, path: Path) -> None:
        """Save the report as JSON."""
        path.write_text(self.to_json(), encoding="utf-8")


def main():
    """CLI entry point: generate a report from a session file."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Generate a holodeck session report")
    parser.add_argument("session_file", help="Path to session JSONL file")
    parser.add_argument("--output", "-o", default=None, help="Output JSON report path")
    args = parser.parse_args()

    session_path = Path(args.session_file)
    if not session_path.exists():
        print(f"Error: {session_path} not found", file=sys.stderr)
        sys.exit(1)

    # Parse session file
    results: list[SimulationResult] = []
    for line in session_path.read_text().strip().split("\n"):
        if not line.strip():
            continue
        data = json.loads(line)
        from holodeck.evaluator import EvalResult

        eval_data = data.get("eval", {})
        ev = EvalResult(
            accuracy=eval_data.get("accuracy", 0),
            specificity=eval_data.get("specificity", 0),
            reasoning=eval_data.get("reasoning", 0),
            completeness=eval_data.get("completeness", 0),
            composite=eval_data.get("composite", 0),
            passed=eval_data.get("passed", False),
            matched_keywords=eval_data.get("matched_keywords", []),
            missed_keywords=eval_data.get("missed_keywords", []),
        )
        results.append(SimulationResult(
            task_type=data["task_type"],
            difficulty=data["difficulty"],
            scenario={},
            response=data.get("response", ""),
            eval_result=ev,
            reflex_compiled=data.get("reflex_compiled", False),
            reflex_id=data.get("reflex_id", ""),
            timestamp=data.get("timestamp", ""),
            response_time_ms=data.get("response_time_ms", 0),
        ))

    report = SessionReport(results)
    print(report.render_text())

    if args.output:
        report.save(Path(args.output))
        print(f"\nReport saved to {args.output}")
