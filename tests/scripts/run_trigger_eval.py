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
Copilot CLI Plugin Trigger Evaluation

Tests whether skill descriptions cause Copilot to activate for the right prompts.

Usage:
    # Test a single skill's trigger accuracy
    uv run tests/scripts/run_trigger_eval.py \
        --eval-set tests/evals/triggers/osdu-qa.json \
        --skill-path skills/osdu-qa

    # Test with multiple runs per query (for reliability)
    uv run tests/scripts/run_trigger_eval.py \
        --eval-set tests/evals/triggers/osdu-qa.json \
        --skill-path skills/osdu-qa \
        --runs-per-query 3

    # Dry run (validate eval set without running Copilot)
    uv run tests/scripts/run_trigger_eval.py \
        --eval-set tests/evals/triggers/osdu-qa.json \
        --skill-path skills/osdu-qa \
        --dry-run
"""

import argparse
import json
import os
import subprocess
import sys
import time
import uuid
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from rich.console import Console
from rich.table import Table

console = Console()

SCRIPT_DIR = Path(__file__).parent
PLUGIN_ROOT = SCRIPT_DIR.parent.parent


def parse_skill_md(skill_path: Path) -> tuple[str, str, str]:
    """Parse a SKILL.md file, returning (name, description, full_content)."""
    content = (skill_path / "SKILL.md").read_text()
    lines = content.split("\n")

    if lines[0].strip() != "---":
        raise ValueError("SKILL.md missing frontmatter")

    end_idx = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        raise ValueError("SKILL.md missing closing frontmatter")

    name = ""
    description = ""
    frontmatter_lines = lines[1:end_idx]
    i = 0
    while i < len(frontmatter_lines):
        line = frontmatter_lines[i]
        if line.startswith("name:"):
            name = line[len("name:"):].strip().strip('"').strip("'")
        elif line.startswith("description:"):
            value = line[len("description:"):].strip()
            if value in (">", "|", ">-", "|-"):
                continuation_lines: list[str] = []
                i += 1
                while i < len(frontmatter_lines) and (
                    frontmatter_lines[i].startswith("  ")
                    or frontmatter_lines[i].startswith("\t")
                ):
                    continuation_lines.append(frontmatter_lines[i].strip())
                    i += 1
                description = " ".join(continuation_lines)
                continue
            else:
                description = value.strip('"').strip("'")
        i += 1

    return name, description, content


def check_copilot_available() -> bool:
    """Check if copilot CLI is available."""
    try:
        result = subprocess.run(
            ["copilot", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def run_single_query_copilot(
    query: str,
    skill_name: str,
    timeout: int,
) -> bool:
    """Run a single query against copilot and detect if the skill was triggered.

    Uses `copilot -p` with JSONL output to detect skill invocation.
    Copilot CLI v1.0+ uses --output-format json (JSONL, one object per line).
    """
    cmd = [
        "copilot",
        "-p", query,
        "--output-format", "json",
    ]

    env = {k: v for k, v in os.environ.items()}

    try:
        # Use temp file to capture full output (subprocess.PIPE can miss events)
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".jsonl", delete=False) as tmp:
            tmp_path = tmp.name

        with open(tmp_path, "w") as outf:
            proc = subprocess.run(
                cmd,
                stdout=outf,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout,
                cwd=str(PLUGIN_ROOT),
                env=env,
            )

        output = Path(tmp_path).read_text()
        Path(tmp_path).unlink(missing_ok=True)

        # Parse JSONL events and look for skill references
        for line in output.split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                event_type = event.get("type", "")
                data = event.get("data", {})

                # Check tool_use events for Skill tool or Read of skill file
                if event_type == "assistant.tool_use":
                    tool_name = data.get("name", "")
                    tool_input = str(data.get("input", {}))
                    if skill_name in tool_input or skill_name in tool_name:
                        return True

                # Check tool execution events (Copilot CLI v1.0+)
                # Copilot triggers skills via: toolName="skill", arguments={"skill":"name"}
                if event_type == "tool.execution_start":
                    tool_name = data.get("toolName", "")
                    arguments = data.get("arguments", {})
                    if tool_name == "skill" and arguments.get("skill") == skill_name:
                        return True
                    # Also check Read/Glob of skill files
                    if skill_name in str(arguments):
                        return True

                # Check tool execution complete for skill loading confirmation
                if event_type == "tool.execution_complete":
                    result_data = data.get("result", {})
                    if skill_name in str(result_data.get("content", "")):
                        return True

                # Check assistant.message for toolRequests containing skill invocation
                if event_type == "assistant.message":
                    for req in data.get("toolRequests", []):
                        if req.get("name") == "skill" and req.get("arguments", {}).get("skill") == skill_name:
                            return True
                        if skill_name in str(req.get("arguments", {})):
                            return True

                # Check reasoning events — Copilot often references the skill
                # in its reasoning before responding inline
                if event_type in ("assistant.reasoning_delta", "assistant.reasoning"):
                    content = data.get("deltaContent", "") or data.get("content", "")
                    # Look for patterns like "glab skill", "invoke the glab",
                    # "use the glab skill", "glab is the expert"
                    content_lower = content.lower()
                    if skill_name in content_lower and (
                        "skill" in content_lower
                        or "invoke" in content_lower
                        or "use the" in content_lower
                        or "expert" in content_lower
                        or "handles" in content_lower
                        or "trigger" in content_lower
                    ):
                        return True

                # Check message deltas for skill file references
                if event_type == "assistant.message_delta":
                    content = data.get("deltaContent", "")
                    if f"skills/{skill_name}" in content:
                        return True
                    if f"/{skill_name}" in content:
                        return True

                # Check for tool results that reference skill files
                if event_type == "assistant.tool_result":
                    result_content = str(data)
                    if f"skills/{skill_name}/SKILL.md" in result_content:
                        return True

            except json.JSONDecodeError:
                continue

        # Fallback: check if reasoning explicitly references the skill by name
        # Copilot often mentions the skill in reasoning without formally invoking it
        if skill_name in output.lower():
            for line in output.split("\n"):
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                    etype = event.get("type", "")
                    data = event.get("data", {})
                    # Reasoning that mentions the skill name with intent to use it
                    if etype in ("assistant.reasoning", "assistant.reasoning_delta"):
                        content = (data.get("content", "") or data.get("deltaContent", "")).lower()
                        if skill_name in content and any(
                            w in content for w in ("skill", "invoke", "use the", "expert", "guidance")
                        ):
                            return True
                    # Message content that demonstrates skill knowledge was applied
                    if etype == "assistant.message":
                        content = data.get("content", "").lower()
                        if skill_name in content and len(content) > 100:
                            return True
                except json.JSONDecodeError:
                    continue

        return False

    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False


def run_single_query_claude(
    query: str,
    skill_name: str,
    skill_description: str,
    timeout: int,
) -> bool:
    """Run a single query using claude -p (fallback when copilot not available).

    Creates a temporary command file so the skill appears in available_skills,
    then checks if claude invokes it.
    """
    unique_id = uuid.uuid4().hex[:8]
    clean_name = f"{skill_name}-eval-{unique_id}"
    commands_dir = PLUGIN_ROOT / ".tmp" / "eval-commands"
    command_file = commands_dir / f"{clean_name}.md"

    try:
        commands_dir.mkdir(parents=True, exist_ok=True)
        indented_desc = "\n  ".join(skill_description.split("\n"))
        command_content = (
            f"---\n"
            f"description: |\n"
            f"  {indented_desc}\n"
            f"---\n\n"
            f"# {skill_name}\n\n"
            f"This skill handles: {skill_description}\n"
        )
        command_file.write_text(command_content)

        cmd = [
            "claude",
            "-p", query,
            "--output-format", "stream-json",
            "--verbose",
            "--include-partial-messages",
        ]

        env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(PLUGIN_ROOT),
            env=env,
        )

        return clean_name in result.stdout

    except (subprocess.TimeoutExpired, Exception):
        return False
    finally:
        if command_file.exists():
            command_file.unlink()


def run_eval(
    eval_set: list[dict],
    skill_name: str,
    description: str,
    num_workers: int,
    timeout: int,
    runs_per_query: int = 1,
    trigger_threshold: float = 0.5,
    use_claude: bool = False,
) -> dict:
    """Run the full eval set and return results."""
    results = []

    run_fn = run_single_query_claude if use_claude else run_single_query_copilot

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        future_to_info = {}
        for item in eval_set:
            for run_idx in range(runs_per_query):
                if use_claude:
                    future = executor.submit(
                        run_fn, item["query"], skill_name, description, timeout
                    )
                else:
                    future = executor.submit(
                        run_fn, item["query"], skill_name, timeout
                    )
                future_to_info[future] = (item, run_idx)

        query_triggers: dict[str, list[bool]] = {}
        query_items: dict[str, dict] = {}
        for future in as_completed(future_to_info):
            item, _ = future_to_info[future]
            query = item["query"]
            query_items[query] = item
            if query not in query_triggers:
                query_triggers[query] = []
            try:
                query_triggers[query].append(future.result())
            except Exception as e:
                print(f"Warning: query failed: {e}", file=sys.stderr)
                query_triggers[query].append(False)

    for query, triggers in query_triggers.items():
        item = query_items[query]
        trigger_rate = sum(triggers) / len(triggers)
        should_trigger = item["should_trigger"]
        if should_trigger:
            did_pass = trigger_rate >= trigger_threshold
        else:
            did_pass = trigger_rate < trigger_threshold
        results.append({
            "query": query,
            "should_trigger": should_trigger,
            "trigger_rate": trigger_rate,
            "triggers": sum(triggers),
            "runs": len(triggers),
            "pass": did_pass,
        })

    passed = sum(1 for r in results if r["pass"])
    total = len(results)

    # Calculate precision/recall
    pos = [r for r in results if r["should_trigger"]]
    neg = [r for r in results if not r["should_trigger"]]
    tp = sum(1 for r in pos if r["trigger_rate"] >= trigger_threshold)
    fn = sum(1 for r in pos if r["trigger_rate"] < trigger_threshold)
    fp = sum(1 for r in neg if r["trigger_rate"] >= trigger_threshold)
    tn = sum(1 for r in neg if r["trigger_rate"] < trigger_threshold)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0.0

    return {
        "skill_name": skill_name,
        "description": description,
        "results": results,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "accuracy": round(accuracy, 3),
        },
    }


def validate_eval_set(eval_set: list[dict]) -> list[str]:
    """Validate an eval set for common issues."""
    issues = []

    if len(eval_set) < 4:
        issues.append(f"Only {len(eval_set)} queries — recommend at least 8 (4 positive, 4 negative)")

    positives = [e for e in eval_set if e.get("should_trigger")]
    negatives = [e for e in eval_set if not e.get("should_trigger")]

    if not positives:
        issues.append("No should_trigger=true queries")
    if not negatives:
        issues.append("No should_trigger=false queries")

    for e in eval_set:
        if "query" not in e:
            issues.append(f"Entry missing 'query' field: {e}")
        if "should_trigger" not in e:
            issues.append(f"Entry missing 'should_trigger' field: {e.get('query', '?')[:50]}")
        if len(e.get("query", "")) < 10:
            issues.append(f"Query too short (should be realistic): {e.get('query', '')}")

    return issues


def display_results(output: dict, verbose: bool = False):
    """Display eval results as a rich table."""
    summary = output["summary"]

    table = Table(title=f"Trigger Eval: {output['skill_name']}")
    table.add_column("Status", justify="center", width=6)
    table.add_column("Expected", justify="center", width=9)
    table.add_column("Rate", justify="right", width=6)
    table.add_column("Query", max_width=70)

    for r in output["results"]:
        status = "[green]PASS[/green]" if r["pass"] else "[red]FAIL[/red]"
        expected = "[green]trigger[/green]" if r["should_trigger"] else "[dim]skip[/dim]"
        rate = f"{r['triggers']}/{r['runs']}"
        table.add_row(status, expected, rate, r["query"][:70])

    console.print(table)
    console.print()
    console.print(
        f"[bold]Results:[/bold] {summary['passed']}/{summary['total']} passed  "
        f"Precision={summary['precision']:.0%}  "
        f"Recall={summary['recall']:.0%}  "
        f"Accuracy={summary['accuracy']:.0%}"
    )


def main():
    parser = argparse.ArgumentParser(description="Run trigger evaluation for a Copilot CLI plugin skill")
    parser.add_argument("--eval-set", required=True, help="Path to trigger-evals.json")
    parser.add_argument("--skill-path", required=True, help="Path to skill directory")
    parser.add_argument("--num-workers", type=int, default=5, help="Parallel workers")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout per query (seconds)")
    parser.add_argument("--runs-per-query", type=int, default=1, help="Runs per query (3 for reliability)")
    parser.add_argument("--trigger-threshold", type=float, default=0.5, help="Trigger rate threshold")
    parser.add_argument("--use-claude", action="store_true", help="Use claude -p instead of copilot (for dev)")
    parser.add_argument("--dry-run", action="store_true", help="Validate eval set without running")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    # Load eval set
    eval_path = Path(args.eval_set)
    if not eval_path.exists():
        console.print(f"[red]Error:[/red] {eval_path} not found")
        raise SystemExit(1)

    data = json.loads(eval_path.read_text())
    eval_set = data if isinstance(data, list) else data.get("evals", [])

    # Load skill
    skill_path = Path(args.skill_path)
    if not (skill_path / "SKILL.md").exists():
        console.print(f"[red]Error:[/red] No SKILL.md at {skill_path}")
        raise SystemExit(1)

    name, description, _ = parse_skill_md(skill_path)

    # Validate eval set
    issues = validate_eval_set(eval_set)
    if issues:
        console.print("[yellow]Eval set issues:[/yellow]")
        for issue in issues:
            console.print(f"  [yellow]WARN:[/yellow] {issue}")
        console.print()

    if args.dry_run:
        console.print(f"[bold]Skill:[/bold] {name}")
        console.print(f"[bold]Description:[/bold] {description[:100]}...")
        console.print(f"[bold]Queries:[/bold] {len(eval_set)} ({sum(1 for e in eval_set if e.get('should_trigger'))} positive, {sum(1 for e in eval_set if not e.get('should_trigger'))} negative)")
        if not issues:
            console.print("[green]Eval set looks good.[/green]")
        raise SystemExit(0)

    # Check CLI availability
    if not args.use_claude and not check_copilot_available():
        console.print("[yellow]copilot CLI not found, falling back to claude -p[/yellow]")
        args.use_claude = True

    if args.use_claude:
        # Verify claude is available
        try:
            subprocess.run(["claude", "--version"], capture_output=True, timeout=5)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            console.print("[red]Error:[/red] Neither copilot nor claude CLI found")
            raise SystemExit(1)

    if args.verbose:
        console.print(f"[blue]Running trigger eval for {name}...[/blue]")
        console.print(f"Using: {'claude -p' if args.use_claude else 'copilot --prompt'}")

    output = run_eval(
        eval_set=eval_set,
        skill_name=name,
        description=description,
        num_workers=args.num_workers,
        timeout=args.timeout,
        runs_per_query=args.runs_per_query,
        trigger_threshold=args.trigger_threshold,
        use_claude=args.use_claude,
    )

    if args.json:
        console.print_json(json.dumps(output, indent=2))
    else:
        display_results(output, args.verbose)

    all_passed = output["summary"]["failed"] == 0
    raise SystemExit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
