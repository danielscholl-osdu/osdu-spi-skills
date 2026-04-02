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
Skill Test Runner — Three-layer testing for a single skill.

Runs all available tests for a skill in order:
  Layer 1: Structure validation (fast, always runs)
  Layer 2: Trigger accuracy (medium, runs if trigger-evals.json exists)
  Layer 3: Session scenarios (slow, runs if matching scenarios exist)

Usage:
    # Test a specific skill (all layers)
    uv run tests/scripts/test_skill.py glab

    # Structure only (fast)
    uv run tests/scripts/test_skill.py glab --layer 1

    # Trigger eval only
    uv run tests/scripts/test_skill.py glab --layer 2

    # Session test only
    uv run tests/scripts/test_skill.py glab --layer 3

    # Test all skills (layer 1 only — fast)
    uv run tests/scripts/test_skill.py --all

    # List what tests exist for each skill
    uv run tests/scripts/test_skill.py --inventory
"""

import json
import subprocess
import sys
import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

SCRIPT_DIR = Path(__file__).parent
PLUGIN_ROOT = SCRIPT_DIR.parent.parent
SKILLS_DIR = PLUGIN_ROOT / "skills"
TRIGGERS_DIR = PLUGIN_ROOT / "tests" / "evals" / "triggers"
SCENARIOS_DIR = PLUGIN_ROOT / "tests" / "evals" / "scenarios"


def run_layer1(skill_name: str) -> dict:
    """Layer 1: Structure validation."""
    skill_dir = SKILLS_DIR / skill_name
    result = {"layer": 1, "name": "structure", "skill": skill_name}

    cmd = [
        sys.executable, str(SCRIPT_DIR / "validate.py"),
        str(skill_dir), "--json",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        data = json.loads(proc.stdout)
        results = data.get("results", [])
        errors = sum(len(r.get("errors", [])) for r in results)
        warnings = sum(len(r.get("warnings", [])) for r in results)
        result["passed"] = errors == 0
        result["errors"] = errors
        result["warnings"] = warnings
        result["details"] = data
    except Exception as e:
        result["passed"] = False
        result["errors"] = 1
        result["warnings"] = 0
        result["error"] = str(e)

    return result


def run_layer2(skill_name: str, cli: str = "claude") -> dict:
    """Layer 2: Trigger accuracy (single-shot)."""
    skill_dir = SKILLS_DIR / skill_name
    eval_file = TRIGGERS_DIR / f"{skill_name}.json"
    result = {"layer": 2, "name": "triggers", "skill": skill_name}

    if not eval_file.exists():
        result["skipped"] = True
        result["reason"] = "No trigger-evals.json"
        return result

    cmd = [
        sys.executable, str(SCRIPT_DIR / "run_trigger_eval.py"),
        "--eval-set", str(eval_file),
        "--skill-path", str(skill_dir),
        "--dry-run",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        # Dry run validates the eval set structure
        result["passed"] = proc.returncode == 0
        result["eval_count"] = 0

        # Count evals
        data = json.loads(eval_file.read_text())
        evals = data if isinstance(data, list) else data.get("evals", [])
        positives = sum(1 for e in evals if e.get("should_trigger"))
        negatives = sum(1 for e in evals if not e.get("should_trigger"))
        result["eval_count"] = len(evals)
        result["positives"] = positives
        result["negatives"] = negatives

        # Validate balance
        result["warnings"] = 0
        if positives < 4:
            result["warnings"] += 1
        if negatives < 4:
            result["warnings"] += 1
        if any(len(e.get("query", "")) < 20 for e in evals):
            result["warnings"] += 1

        result["errors"] = 0

    except Exception as e:
        result["passed"] = False
        result["error"] = str(e)

    return result


def run_layer3(skill_name: str, cli: str = "claude") -> dict:
    """Layer 3: Session scenarios (multi-turn via tmux)."""
    result = {"layer": 3, "name": "session", "skill": skill_name}

    # Find matching scenarios
    scenarios = []
    if SCENARIOS_DIR.is_dir():
        for f in SCENARIOS_DIR.glob("*.json"):
            name = f.stem
            if skill_name in name:
                scenarios.append(f)

    if not scenarios:
        result["skipped"] = True
        result["reason"] = "No matching scenarios"
        return result

    result["scenarios"] = []
    all_passed = True

    for scenario_path in scenarios:
        cmd = [
            sys.executable, str(SCRIPT_DIR / "session_test.py"),
            "--scenario", str(scenario_path),
            "--cli", cli,
            "--json",
            "--timeout-response", "90",
            "--timeout-ready", "30",
        ]
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=600,
            )
            data = json.loads(proc.stdout)
            summary = data.get("summary", {})
            scenario_result = {
                "file": scenario_path.name,
                "passed": summary.get("failed", 1) == 0,
                "steps_passed": summary.get("passed", 0),
                "steps_total": summary.get("total_steps", 0),
                "duration": data.get("duration_seconds", 0),
            }
            if not scenario_result["passed"]:
                all_passed = False
                # Collect failures
                scenario_result["failures"] = [
                    {
                        "step": s["name"],
                        "prompt": s["prompt"],
                        "failed_assertions": [
                            a for a in s.get("assertions", []) if not a["passed"]
                        ],
                    }
                    for s in data.get("steps", [])
                    if not s["passed"]
                ]
            result["scenarios"].append(scenario_result)
        except subprocess.TimeoutExpired:
            result["scenarios"].append({
                "file": scenario_path.name,
                "passed": False,
                "error": "Timeout (600s)",
            })
            all_passed = False
        except Exception as e:
            result["scenarios"].append({
                "file": scenario_path.name,
                "passed": False,
                "error": str(e),
            })
            all_passed = False

    result["passed"] = all_passed
    return result


def get_inventory() -> list[dict]:
    """Get test inventory for all skills."""
    inventory = []
    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir() or not (skill_dir / "SKILL.md").exists():
            continue

        name = skill_dir.name
        has_triggers = (TRIGGERS_DIR / f"{name}.json").exists()

        scenarios = []
        if SCENARIOS_DIR.is_dir():
            scenarios = [f.name for f in SCENARIOS_DIR.glob(f"*{name}*.json")]

        trigger_count = 0
        if has_triggers:
            data = json.loads((TRIGGERS_DIR / f"{name}.json").read_text())
            evals = data if isinstance(data, list) else data.get("evals", [])
            trigger_count = len(evals)

        inventory.append({
            "skill": name,
            "layer1": True,
            "layer2": has_triggers,
            "layer2_count": trigger_count,
            "layer3": len(scenarios) > 0,
            "layer3_scenarios": scenarios,
        })

    return inventory


def display_inventory(inventory: list[dict]):
    """Display test inventory."""
    table = Table(title="Skill Test Inventory")
    table.add_column("Skill", style="cyan")
    table.add_column("L1 Structure", justify="center")
    table.add_column("L2 Triggers", justify="center")
    table.add_column("L3 Sessions", justify="center")

    for item in inventory:
        l1 = "[green]yes[/green]"
        l2 = f"[green]{item['layer2_count']}[/green]" if item["layer2"] else "[dim]—[/dim]"
        l3 = f"[green]{len(item['layer3_scenarios'])}[/green]" if item["layer3"] else "[dim]—[/dim]"
        table.add_row(item["skill"], l1, l2, l3)

    console.print(table)

    # Summary
    total = len(inventory)
    with_triggers = sum(1 for i in inventory if i["layer2"])
    with_sessions = sum(1 for i in inventory if i["layer3"])
    console.print(
        f"\n{total} skills | "
        f"{with_triggers} with trigger evals | "
        f"{with_sessions} with session scenarios"
    )


def display_results(results: list[dict]):
    """Display test results."""
    table = Table(title="Skill Test Results")
    table.add_column("Layer", justify="center", width=8)
    table.add_column("Test", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Details")

    for r in results:
        if r.get("skipped"):
            table.add_row(
                f"L{r['layer']}", r["name"],
                "[dim]SKIP[/dim]", r.get("reason", "")
            )
            continue

        status = "[green]PASS[/green]" if r.get("passed") else "[red]FAIL[/red]"

        if r["layer"] == 1:
            detail = f"{r.get('errors', 0)} errors, {r.get('warnings', 0)} warnings"
        elif r["layer"] == 2:
            detail = f"{r.get('eval_count', 0)} queries ({r.get('positives', 0)}+/{r.get('negatives', 0)}-)"
        elif r["layer"] == 3:
            scenarios = r.get("scenarios", [])
            if scenarios:
                total_steps = sum(s.get("steps_total", 0) for s in scenarios)
                passed_steps = sum(s.get("steps_passed", 0) for s in scenarios)
                duration = sum(s.get("duration", 0) for s in scenarios)
                detail = f"{passed_steps}/{total_steps} steps, {duration:.0f}s"
            else:
                detail = r.get("error", "unknown")
        else:
            detail = ""

        table.add_row(f"L{r['layer']}", r["name"], status, detail)

    console.print(table)

    # Overall
    ran = [r for r in results if not r.get("skipped")]
    passed = sum(1 for r in ran if r.get("passed"))
    console.print(f"\n[bold]Overall:[/bold] {passed}/{len(ran)} layers passed")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Three-layer skill test runner")
    parser.add_argument("skill", nargs="?", help="Skill name to test")
    parser.add_argument("--layer", type=int, choices=[1, 2, 3], help="Run only this layer")
    parser.add_argument("--all", action="store_true", help="Test all skills (layer 1 only)")
    parser.add_argument("--inventory", action="store_true", help="Show test inventory")
    parser.add_argument("--cli", default="claude", choices=["copilot", "claude"], help="CLI for layers 2/3")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    if args.inventory:
        inv = get_inventory()
        if args.json:
            console.print_json(json.dumps(inv, indent=2))
        else:
            display_inventory(inv)
        raise SystemExit(0)

    if args.all:
        # Run layer 1 on all skills
        results = []
        for skill_dir in sorted(SKILLS_DIR.iterdir()):
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                results.append(run_layer1(skill_dir.name))

        if args.json:
            console.print_json(json.dumps(results, indent=2))
        else:
            table = Table(title="All Skills — Structure Validation")
            table.add_column("Skill", style="cyan")
            table.add_column("Status", justify="center")
            table.add_column("Errors", justify="right", style="red")
            table.add_column("Warnings", justify="right", style="yellow")
            for r in results:
                status = "[green]PASS[/green]" if r["passed"] else "[red]FAIL[/red]"
                table.add_row(r["skill"], status, str(r.get("errors", 0)), str(r.get("warnings", 0)))
            console.print(table)
            passed = sum(1 for r in results if r["passed"])
            console.print(f"\n{passed}/{len(results)} skills passed structure validation")
        raise SystemExit(0 if all(r["passed"] for r in results) else 1)

    if not args.skill:
        parser.error("Provide a skill name, --all, or --inventory")

    # Verify skill exists
    skill_dir = SKILLS_DIR / args.skill
    if not skill_dir.is_dir() or not (skill_dir / "SKILL.md").exists():
        console.print(f"[red]Error:[/red] Skill '{args.skill}' not found at {skill_dir}")
        raise SystemExit(1)

    # Run requested layers
    results = []
    layers = [args.layer] if args.layer else [1, 2, 3]

    for layer in layers:
        if layer == 1:
            results.append(run_layer1(args.skill))
        elif layer == 2:
            results.append(run_layer2(args.skill, args.cli))
        elif layer == 3:
            results.append(run_layer3(args.skill, args.cli))

    if args.json:
        console.print_json(json.dumps(results, indent=2))
    else:
        display_results(results)

    ran = [r for r in results if not r.get("skipped")]
    all_passed = all(r.get("passed") for r in ran)
    raise SystemExit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
