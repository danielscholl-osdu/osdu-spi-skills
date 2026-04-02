# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "rich",
# ]
# ///
# Copyright 2026, Microsoft
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Skill Value Comparator — Does the skill actually help?

Runs the same scenario twice:
  1. with_skill  — skill SKILL.md present (normal)
  2. without_skill — skill SKILL.md temporarily hidden

Compares assertion pass rates to measure whether the skill adds value,
adds nothing, or actually hurts.

Usage:
    # Compare glab skill value
    uv run tests/scripts/compare_skill.py \
        --skill glab \
        --scenario tests/evals/scenarios/glab-workflow.json

    # Compare with multiple runs for reliability
    uv run tests/scripts/compare_skill.py \
        --skill glab \
        --scenario tests/evals/scenarios/glab-workflow.json \
        --runs 3

    # Save results for tracking over time
    uv run tests/scripts/compare_skill.py \
        --skill glab \
        --scenario tests/evals/scenarios/glab-workflow.json \
        --save-to tests/benchmarks/
"""

import json
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

SCRIPT_DIR = Path(__file__).parent
PLUGIN_ROOT = SCRIPT_DIR.parent.parent
SKILLS_DIR = PLUGIN_ROOT / "skills"


def run_scenario(scenario_path: str, cli: str, timeout: int = 600) -> dict:
    """Run a session scenario and return results."""
    cmd = [
        sys.executable, str(SCRIPT_DIR / "session_test.py"),
        "--scenario", scenario_path,
        "--cli", cli,
        "--json",
        "--timeout-response", "90",
        "--timeout-ready", "30",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"error": proc.stderr or proc.stdout, "steps": [], "summary": {}}


def hide_skill(skill_dir: Path) -> Path:
    """Temporarily hide a skill by renaming SKILL.md."""
    skill_md = skill_dir / "SKILL.md"
    hidden = skill_dir / "SKILL.md.hidden"
    if skill_md.exists():
        shutil.move(str(skill_md), str(hidden))
    return hidden


def restore_skill(skill_dir: Path) -> None:
    """Restore a hidden skill."""
    hidden = skill_dir / "SKILL.md.hidden"
    skill_md = skill_dir / "SKILL.md"
    if hidden.exists():
        shutil.move(str(hidden), str(skill_md))


def extract_metrics(results: dict) -> dict:
    """Extract comparable metrics from scenario results."""
    steps = results.get("steps", [])
    total_assertions = 0
    passed_assertions = 0
    step_results = []

    for step in steps:
        assertions = step.get("assertions", [])
        step_passed = sum(1 for a in assertions if a.get("passed"))
        step_total = len(assertions)
        total_assertions += step_total
        passed_assertions += step_passed

        step_results.append({
            "name": step.get("name", "unknown"),
            "passed": step_passed,
            "total": step_total,
            "pass_rate": step_passed / step_total if step_total > 0 else 1.0,
            "assertion_details": [
                {
                    "description": a.get("description", ""),
                    "passed": a.get("passed", False),
                    "evidence": a.get("evidence", ""),
                }
                for a in assertions
            ],
        })

    pass_rate = passed_assertions / total_assertions if total_assertions > 0 else 0.0

    return {
        "total_assertions": total_assertions,
        "passed_assertions": passed_assertions,
        "pass_rate": pass_rate,
        "duration": results.get("duration_seconds", 0),
        "steps": step_results,
        "error": results.get("error"),
    }


def aggregate_runs(runs: list[dict]) -> dict:
    """Aggregate metrics across multiple runs."""
    if not runs:
        return {"mean_pass_rate": 0, "runs": 0}

    pass_rates = [r["pass_rate"] for r in runs]
    durations = [r["duration"] for r in runs]

    n = len(pass_rates)
    mean_pr = sum(pass_rates) / n
    mean_dur = sum(durations) / n

    if n > 1:
        import math
        variance = sum((x - mean_pr) ** 2 for x in pass_rates) / (n - 1)
        stddev_pr = math.sqrt(variance)
    else:
        stddev_pr = 0.0

    return {
        "runs": n,
        "mean_pass_rate": round(mean_pr, 4),
        "stddev_pass_rate": round(stddev_pr, 4),
        "min_pass_rate": round(min(pass_rates), 4),
        "max_pass_rate": round(max(pass_rates), 4),
        "mean_duration": round(mean_dur, 1),
        "individual_runs": runs,
    }


def run_comparison(
    skill_name: str,
    scenario_path: str,
    cli: str,
    num_runs: int,
    verbose: bool,
) -> dict:
    """Run with_skill and without_skill comparison."""
    skill_dir = SKILLS_DIR / skill_name

    if not (skill_dir / "SKILL.md").exists():
        return {"error": f"Skill '{skill_name}' not found"}

    comparison = {
        "skill_name": skill_name,
        "scenario": Path(scenario_path).stem,
        "cli": cli,
        "num_runs": num_runs,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "with_skill": [],
        "without_skill": [],
    }

    # Phase 1: with_skill runs
    if verbose:
        console.print(f"\n[bold blue]Phase 1: with_skill ({num_runs} run{'s' if num_runs > 1 else ''})[/bold blue]")

    for i in range(num_runs):
        if verbose:
            console.print(f"  Run {i + 1}/{num_runs}...", end=" ")
        raw = run_scenario(scenario_path, cli)
        metrics = extract_metrics(raw)
        comparison["with_skill"].append(metrics)
        if verbose:
            console.print(f"[green]{metrics['pass_rate']:.0%}[/green] ({metrics['duration']:.0f}s)")

    # Phase 2: without_skill runs
    if verbose:
        console.print(f"\n[bold blue]Phase 2: without_skill ({num_runs} run{'s' if num_runs > 1 else ''})[/bold blue]")
        console.print(f"  [dim]Temporarily hiding {skill_dir}/SKILL.md[/dim]")

    hidden_path = hide_skill(skill_dir)

    try:
        for i in range(num_runs):
            if verbose:
                console.print(f"  Run {i + 1}/{num_runs}...", end=" ")
            raw = run_scenario(scenario_path, cli)
            metrics = extract_metrics(raw)
            comparison["without_skill"].append(metrics)
            if verbose:
                console.print(f"[yellow]{metrics['pass_rate']:.0%}[/yellow] ({metrics['duration']:.0f}s)")
    finally:
        # ALWAYS restore the skill, even on error/interrupt
        restore_skill(skill_dir)
        if verbose:
            console.print(f"  [dim]Restored {skill_dir}/SKILL.md[/dim]")

    # Aggregate
    with_agg = aggregate_runs(comparison["with_skill"])
    without_agg = aggregate_runs(comparison["without_skill"])

    delta = round(with_agg["mean_pass_rate"] - without_agg["mean_pass_rate"], 4)

    comparison["summary"] = {
        "with_skill": with_agg,
        "without_skill": without_agg,
        "delta_pass_rate": delta,
        "verdict": classify_verdict(delta, with_agg, without_agg),
    }

    return comparison


def classify_verdict(delta: float, with_agg: dict, without_agg: dict) -> dict:
    """Classify the skill's value based on comparison results."""
    with_pr = with_agg["mean_pass_rate"]
    without_pr = without_agg["mean_pass_rate"]

    if delta > 0.1:
        verdict = "VALUABLE"
        explanation = (
            f"Skill improves pass rate by {delta:+.0%}. "
            f"Keep it — the model needs these instructions."
        )
        action = "keep"
    elif delta > 0.0:
        verdict = "MARGINAL"
        explanation = (
            f"Skill improves pass rate by {delta:+.0%}. "
            f"Small benefit — consider if the context cost is worth it."
        )
        action = "review"
    elif delta == 0.0:
        if with_pr >= 0.95:
            verdict = "REDUNDANT"
            explanation = (
                f"Both with and without score {with_pr:.0%}. "
                f"Model already knows this — skill is context bloat."
            )
            action = "consider_removing"
        else:
            verdict = "INEFFECTIVE"
            explanation = (
                f"Both with and without score {with_pr:.0%}. "
                f"Skill isn't helping, but the model also struggles. Rewrite the skill."
            )
            action = "rewrite"
    else:
        verdict = "HARMFUL"
        explanation = (
            f"Skill HURTS by {delta:+.0%}. "
            f"Without: {without_pr:.0%}, With: {with_pr:.0%}. "
            f"Skill overrides correct behavior with wrong instructions."
        )
        action = "remove_or_rewrite"

    return {
        "verdict": verdict,
        "explanation": explanation,
        "action": action,
    }


def display_comparison(comparison: dict):
    """Display comparison results."""
    summary = comparison.get("summary", {})
    with_agg = summary.get("with_skill", {})
    without_agg = summary.get("without_skill", {})
    verdict = summary.get("verdict", {})

    # Header
    console.print()
    verdict_color = {
        "VALUABLE": "green",
        "MARGINAL": "yellow",
        "REDUNDANT": "yellow",
        "INEFFECTIVE": "red",
        "HARMFUL": "red bold",
    }.get(verdict.get("verdict", ""), "white")

    console.print(Panel(
        f"[{verdict_color}]{verdict.get('verdict', '?')}[/{verdict_color}]\n\n"
        f"{verdict.get('explanation', '')}",
        title=f"Skill Value: {comparison['skill_name']}",
        subtitle=f"Scenario: {comparison['scenario']} | CLI: {comparison['cli']}",
    ))

    # Comparison table
    table = Table(title="Pass Rate Comparison")
    table.add_column("Metric", style="cyan")
    table.add_column("With Skill", justify="right")
    table.add_column("Without Skill", justify="right")
    table.add_column("Delta", justify="right")

    delta_pr = summary.get("delta_pass_rate", 0)
    delta_color = "green" if delta_pr > 0 else "red" if delta_pr < 0 else "dim"

    table.add_row(
        "Pass Rate",
        f"{with_agg.get('mean_pass_rate', 0):.0%}" + (f" ± {with_agg.get('stddev_pass_rate', 0):.0%}" if with_agg.get("runs", 0) > 1 else ""),
        f"{without_agg.get('mean_pass_rate', 0):.0%}" + (f" ± {without_agg.get('stddev_pass_rate', 0):.0%}" if without_agg.get("runs", 0) > 1 else ""),
        f"[{delta_color}]{delta_pr:+.0%}[/{delta_color}]",
    )
    table.add_row(
        "Duration",
        f"{with_agg.get('mean_duration', 0):.0f}s",
        f"{without_agg.get('mean_duration', 0):.0f}s",
        f"{with_agg.get('mean_duration', 0) - without_agg.get('mean_duration', 0):+.0f}s",
    )
    table.add_row(
        "Runs",
        str(with_agg.get("runs", 0)),
        str(without_agg.get("runs", 0)),
        "",
    )

    console.print(table)

    # Per-assertion breakdown (from first run of each)
    with_steps = comparison.get("with_skill", [{}])[0].get("steps", [])
    without_steps = comparison.get("without_skill", [{}])[0].get("steps", [])

    if with_steps and without_steps:
        console.print()
        detail_table = Table(title="Per-Assertion Breakdown (first run)")
        detail_table.add_column("Step", style="cyan")
        detail_table.add_column("Assertion")
        detail_table.add_column("With", justify="center", width=6)
        detail_table.add_column("Without", justify="center", width=9)
        detail_table.add_column("Skill Needed?", justify="center")

        for w_step, wo_step in zip(with_steps, without_steps):
            for w_a, wo_a in zip(
                w_step.get("assertion_details", []),
                wo_step.get("assertion_details", []),
            ):
                w_pass = w_a.get("passed", False)
                wo_pass = wo_a.get("passed", False)

                w_str = "[green]PASS[/green]" if w_pass else "[red]FAIL[/red]"
                wo_str = "[green]PASS[/green]" if wo_pass else "[red]FAIL[/red]"

                if w_pass and not wo_pass:
                    needed = "[green bold]YES[/green bold]"
                elif w_pass and wo_pass:
                    needed = "[dim]no[/dim]"
                elif not w_pass and wo_pass:
                    needed = "[red]HURTS[/red]"
                else:
                    needed = "[yellow]both fail[/yellow]"

                detail_table.add_row(
                    w_step["name"],
                    w_a.get("description", "")[:50],
                    w_str,
                    wo_str,
                    needed,
                )

        console.print(detail_table)

    # Action recommendation
    action = verdict.get("action", "")
    if action == "keep":
        console.print("\n[green]Action: Keep the skill as-is.[/green]")
    elif action == "review":
        console.print("\n[yellow]Action: Review — small benefit. Check if context cost is justified.[/yellow]")
    elif action == "consider_removing":
        console.print("\n[yellow]Action: Consider removing — model handles this without help.[/yellow]")
    elif action == "rewrite":
        console.print("\n[yellow]Action: Rewrite — skill isn't helping but model also struggles.[/yellow]")
    elif action == "remove_or_rewrite":
        console.print("\n[red]Action: Remove or completely rewrite — skill is making things worse.[/red]")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Compare skill value: with vs without")
    parser.add_argument("--skill", required=True, help="Skill name to compare")
    parser.add_argument("--scenario", required=True, help="Path to scenario JSON")
    parser.add_argument("--runs", type=int, default=1, help="Runs per configuration (3 recommended for reliability)")
    parser.add_argument("--cli", default="claude", choices=["copilot", "claude"], help="CLI to test with")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--verbose", action="store_true", help="Show progress")
    parser.add_argument("--save-to", help="Save results to this directory")
    args = parser.parse_args()

    if not Path(args.scenario).exists():
        console.print(f"[red]Error:[/red] Scenario not found: {args.scenario}")
        raise SystemExit(1)

    skill_dir = SKILLS_DIR / args.skill
    if not (skill_dir / "SKILL.md").exists():
        console.print(f"[red]Error:[/red] Skill not found: {args.skill}")
        raise SystemExit(1)

    console.print(Panel(
        f"Skill: [bold]{args.skill}[/bold]\n"
        f"Scenario: {Path(args.scenario).stem}\n"
        f"Runs: {args.runs} per config ({args.runs * 2} total)\n"
        f"CLI: {args.cli}",
        title="Skill Value Comparison",
    ))

    comparison = run_comparison(
        skill_name=args.skill,
        scenario_path=args.scenario,
        cli=args.cli,
        num_runs=args.runs,
        verbose=args.verbose or not args.json,
    )

    if args.json:
        console.print_json(json.dumps(comparison, indent=2, default=str))
    else:
        display_comparison(comparison)

    # Save results
    if args.save_to:
        save_dir = Path(args.save_to)
        save_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{args.skill}_{Path(args.scenario).stem}_{timestamp}.json"
        save_path = save_dir / filename
        save_path.write_text(json.dumps(comparison, indent=2, default=str))
        console.print(f"\n[dim]Results saved to {save_path}[/dim]")

    # Exit code based on verdict
    action = comparison.get("summary", {}).get("verdict", {}).get("action", "")
    if action in ("remove_or_rewrite", ):
        raise SystemExit(2)  # skill is harmful
    elif action in ("consider_removing", "rewrite"):
        raise SystemExit(1)  # skill needs attention
    else:
        raise SystemExit(0)


if __name__ == "__main__":
    main()
