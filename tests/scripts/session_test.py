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
Copilot CLI Session Tester — Multi-prompt testing via tmux.

Launches a Copilot (or Claude) CLI session in a tmux pane, sends a sequence
of prompts, captures output after each, and checks for expected patterns.

This tests things single-shot can't: multi-turn context, agent delegation
chains, routing accuracy across a session, and skill interaction flows.

Usage:
    # Run a test scenario
    uv run tests/scripts/session_test.py \
        --scenario tests/evals/scenarios/routing-basic.json

    # Use claude instead of copilot
    uv run tests/scripts/session_test.py \
        --scenario tests/evals/scenarios/routing-basic.json \
        --cli claude

    # Dry run — show what would happen
    uv run tests/scripts/session_test.py \
        --scenario tests/evals/scenarios/routing-basic.json \
        --dry-run
"""

import json
import os
import re
import subprocess
import sys
import time
import uuid
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

SCRIPT_DIR = Path(__file__).parent
PLUGIN_ROOT = SCRIPT_DIR.parent.parent

# Tmux session naming
SESSION_PREFIX = "copilot-test"


# =============================================================================
# Tmux Helpers
# =============================================================================

def tmux_cmd(*args: str, capture: bool = True) -> str:
    """Run a tmux command and return output."""
    cmd = ["tmux"] + list(args)
    result = subprocess.run(cmd, capture_output=capture, text=True, timeout=10)
    if result.returncode != 0 and capture:
        raise RuntimeError(f"tmux failed: {result.stderr.strip()}")
    return result.stdout.strip() if capture else ""


def validate_prompts_readonly(steps: list[dict]) -> list[str]:
    """Check that scenario prompts are read-only (questions, not actions).

    Integration tests run with --dangerously-skip-permissions so prompts
    must NOT request destructive or write operations.
    """
    # These patterns detect IMPERATIVE actions (commands to do something),
    # not mentions of concepts. "what merge requests" is fine;
    # "create a merge request" is not.
    action_patterns = [
        (r"^(create|make|add|write|delete|remove|drop|push|deploy|install)\s", "starts with action verb"),
        (r"\b(run|execute|deploy|build)\s+(the|a|my|all|this)\b", "execution command"),
        (r"\bglab\s+(mr\s+create|mr\s+merge|ci\s+run|ci\s+retry)\b", "glab write command"),
        (r"\bgit\s+(push|commit|reset|checkout|rebase)\b", "git write command"),
        (r"\b(send|ship|submit)\s+(it|this|the|my)\b", "ship/send command"),
    ]
    issues = []
    for step in steps:
        prompt = step.get("prompt", "").lower()
        for pattern, label in action_patterns:
            if re.search(pattern, prompt):
                issues.append(
                    f"Step '{step.get('name', '?')}': prompt contains {label} "
                    f"— integration tests must be read-only. "
                    f"Prompt: {step['prompt'][:60]}"
                )
                break  # one issue per step is enough
    return issues


def create_session(session_name: str, cli: str, cwd: str, skip_permissions: bool = False) -> None:
    """Create a new tmux session running the CLI."""
    # Start detached session with a shell first
    tmux_cmd(
        "new-session", "-d",
        "-s", session_name,
        "-x", "200", "-y", "50",
    )
    # Build CLI command with optional permission skip for test sessions
    cli_cmd = cli
    if skip_permissions:
        if cli == "claude":
            cli_cmd = f"{cli} --dangerously-skip-permissions"
        elif cli == "copilot":
            cli_cmd = f"{cli} --yolo"
    # Set the working directory and launch the CLI
    tmux_cmd("send-keys", "-t", session_name, f"cd {cwd} && {cli_cmd}", "Enter")


def wake_pane(session_name: str) -> None:
    """Wake a detached tmux pane by triggering SIGWINCH via resize.

    TUI applications (Claude Code, Copilot) running in detached tmux sessions
    don't process stdin until a terminal event occurs. Bumping the window size
    triggers SIGWINCH which wakes the event loop.
    """
    try:
        # Bump width +1 then restore
        tmux_cmd("resize-window", "-t", session_name, "-x", "201", capture=False)
        time.sleep(0.05)
        tmux_cmd("resize-window", "-t", session_name, "-x", "200", capture=False)
    except (RuntimeError, subprocess.TimeoutExpired):
        pass


def send_prompt(session_name: str, prompt: str, cli: str = "copilot") -> None:
    """Send a prompt to the session and submit it.

    Sends a prompt to the tmux session:
    1. Send text with send-keys -l (literal mode, avoids key interpretation)
    2. Debounce — wait for terminal to process the text
    3. Send Enter (claude) or Ctrl+S (copilot) to submit
    4. Wake the pane with SIGWINCH in case it's detached

    The debounce scales with message length: 200ms base + 100ms per KB.
    """
    # Calculate debounce based on message length
    debounce_ms = 200 + (len(prompt) // 1024) * 100
    debounce_ms = min(debounce_ms, 1500)

    # Send text in chunks if long (tmux has argument length limits)
    chunk_size = 512
    for i in range(0, len(prompt), chunk_size):
        chunk = prompt[i:i + chunk_size]
        # -l flag = literal mode, sends text as-is without key interpretation
        tmux_cmd("send-keys", "-t", session_name, "-l", chunk)
        if i + chunk_size < len(prompt):
            time.sleep(0.01)  # 10ms inter-chunk delay

    # Debounce — let the terminal process the pasted text
    time.sleep(debounce_ms / 1000.0)

    # Submit
    if cli == "copilot":
        tmux_cmd("send-keys", "-t", session_name, "C-s")
    else:
        tmux_cmd("send-keys", "-t", session_name, "Enter")

    # Wake the pane (triggers SIGWINCH so TUI processes the input)
    time.sleep(0.1)
    wake_pane(session_name)


def capture_pane(session_name: str, history: int = 2000) -> str:
    """Capture the current pane content including scrollback."""
    return tmux_cmd("capture-pane", "-t", session_name, "-p", "-S", f"-{history}")


def kill_session(session_name: str) -> None:
    """Kill a tmux session."""
    try:
        tmux_cmd("kill-session", "-t", session_name)
    except (RuntimeError, subprocess.TimeoutExpired):
        pass


def session_exists(session_name: str) -> bool:
    """Check if a tmux session exists."""
    try:
        tmux_cmd("has-session", "-t", session_name)
        return True
    except RuntimeError:
        return False


# =============================================================================
# Wait Strategies
# =============================================================================

def get_pane_command(session_name: str) -> str:
    """Get the current foreground command running in the tmux pane.

    Returns process name like 'bash', 'copilot', 'claude', 'node', etc.
    """
    try:
        return tmux_cmd("display-message", "-t", session_name, "-p", "#{pane_current_command}")
    except RuntimeError:
        return ""


def wait_for_cli_process(session_name: str, cli: str, timeout: int = 30) -> bool:
    """Wait until the CLI process is the foreground command in the pane.

    Uses tmux's #{pane_current_command} to detect when a coding agent is running.
    """
    start = time.time()
    while time.time() - start < timeout:
        cmd = get_pane_command(session_name)
        if cli in cmd:
            return True
        time.sleep(0.5)
    return False


def wait_for_ready(
    session_name: str,
    ready_pattern: str,
    timeout: int = 60,
    poll_interval: float = 1.0,
    cli: str = "copilot",
) -> bool:
    """Wait until the CLI is fully loaded and ready for input.

    Two-phase detection:
    1. Wait for the CLI process to become the foreground command
    2. Wait for the CLI-specific ready signal in pane content
    """
    start = time.time()

    # Phase 1: Wait for CLI process to start (best-effort, don't fail on this)
    remaining = timeout - (time.time() - start)
    wait_for_cli_process(session_name, cli, timeout=min(int(remaining), 15))

    # Phase 2: Wait for CLI-specific ready signals
    while time.time() - start < timeout:
        output = capture_pane(session_name)

        if cli == "copilot":
            # Copilot shows this when fully loaded with plugins/skills
            if "Environment loaded" in output or "Describe a task" in output:
                time.sleep(1.0)
                return True
        else:
            # Claude Code: welcome screen with prompt
            if "Welcome" in output or re.search(ready_pattern, output):
                time.sleep(0.5)
                return True

        time.sleep(poll_interval)
    return False


def is_cli_busy(pane_content: str) -> bool:
    """Detect if the CLI is still processing (not ready for input).

    Claude Code shows these indicators while working:
    - "Sprouting…" / "Doing…" / "Reading…" / "Thinking…"
    - Tool execution spinners (✶, ✽, ·, ○)
    - "Press up to edit queued messages" (prompt is queued, not processed)

    Copilot shows similar busy indicators.
    """
    # Check last 10 lines for busy indicators
    tail_lines = pane_content.strip().split("\n")[-10:]
    tail = "\n".join(tail_lines)

    busy_patterns = [
        # Claude Code indicators
        r"Sprouting",
        r"Doing",
        r"Reading",
        r"Thinking",
        r"Searching",
        r"Planning",
        r"Generating",
        r"Analyzing",
        r"Running",
        r"queued messages",
        r"[✶✽·○●] \w",        # spinner characters followed by status word
        # Copilot indicators
        r"Loading",
        r"Working",
        r"Calling",
        r"Waiting",
        r"\.{3}$",             # trailing ellipsis (thinking...)
    ]

    for pattern in busy_patterns:
        if re.search(pattern, tail, re.IGNORECASE):
            return True

    return False


def is_cli_ready(pane_content: str) -> bool:
    """Detect if the CLI is at a clean input prompt, ready for the next command.

    Claude Code: clean `❯` at the end with no busy indicator
    Copilot: similar prompt indicator
    """
    lines = pane_content.strip().split("\n")
    if not lines:
        return False

    # Look at the last few non-empty lines
    tail_lines = [l for l in lines[-5:] if l.strip()]
    if not tail_lines:
        return False

    last_line = tail_lines[-1].strip()

    # Claude Code prompt: line starts with or contains ❯ and nothing after it
    # (or just whitespace/control chars after it)
    if re.search(r"❯\s*$", last_line):
        return not is_cli_busy(pane_content)

    # Generic prompt patterns (for copilot or shell)
    if re.search(r"[>$❯]\s*$", last_line):
        return not is_cli_busy(pane_content)

    return False


def count_content_lines(pane: str, previous: str) -> int:
    """Count how many new non-empty lines appeared since previous capture."""
    prev_lines = set(previous.strip().split("\n"))
    new_lines = [l for l in pane.strip().split("\n") if l.strip() and l not in prev_lines]
    return len(new_lines)


def wait_for_response(
    session_name: str,
    ready_pattern: str,
    previous_output: str,
    timeout: int = 120,
    poll_interval: float = 2.0,
    idle_threshold: float = 10.0,
    min_response_lines: int = 3,
) -> str:
    """Wait for the CLI to finish responding and return the new output.

    Detection strategy (works for both Claude Code and Copilot):
    1. Wait for substantial new content (not just our prompt echoed back)
    2. Watch for busy indicators to appear and disappear
    3. If no busy indicators, wait for content to stabilize
    4. Require at least min_response_lines of new content before considering done

    The key insight: both CLIs show the prompt character (❯ or >) from startup.
    We can't rely on "prompt appeared" to mean "response done." Instead we
    track content volume and stabilization.
    """
    start = time.time()
    last_output = previous_output
    last_change = time.time()
    saw_busy = False
    saw_substantial_content = False
    peak_new_lines = 0

    while time.time() - start < timeout:
        current = capture_pane(session_name)

        # Track content changes
        if current != last_output:
            last_output = current
            last_change = time.time()

            # Count new content lines
            new_lines = count_content_lines(current, previous_output)
            peak_new_lines = max(peak_new_lines, new_lines)

            if new_lines >= min_response_lines:
                saw_substantial_content = True

            # Check for busy indicators
            if is_cli_busy(current):
                saw_busy = True

        # Only consider "done" if we have substantial content
        if saw_substantial_content:
            idle_time = time.time() - last_change

            # If we saw busy and it cleared, done
            if saw_busy and not is_cli_busy(current) and is_cli_ready(current):
                time.sleep(0.5)
                return capture_pane(session_name)

            # If content stabilized for a while (no busy indicators needed)
            # This handles CLIs that don't show explicit busy indicators
            if idle_time > idle_threshold:
                return current

        # Even without substantial content, don't wait forever
        # (handles case where response is very short)
        if time.time() - start > timeout * 0.8:
            if current != previous_output:
                return current

        time.sleep(poll_interval)

    return last_output


# =============================================================================
# Pattern Matching
# =============================================================================

def check_assertions(output: str, assertions: list[dict]) -> list[dict]:
    """Check assertions against captured output.

    Each assertion has:
    - pattern: regex or substring to search for
    - type: "contains", "regex", "not_contains"
    - description: human-readable description
    """
    results = []
    for assertion in assertions:
        desc = assertion.get("description", assertion.get("pattern", ""))
        pattern = assertion["pattern"]
        assert_type = assertion.get("type", "contains")

        if assert_type == "contains":
            passed = pattern.lower() in output.lower()
            evidence = f"Found '{pattern}'" if passed else f"'{pattern}' not found in output"
        elif assert_type == "regex":
            match = re.search(pattern, output, re.IGNORECASE | re.MULTILINE)
            passed = match is not None
            evidence = f"Matched: {match.group(0)[:80]}" if passed else f"Pattern /{pattern}/ not matched"
        elif assert_type == "not_contains":
            passed = pattern.lower() not in output.lower()
            evidence = f"Correctly absent" if passed else f"Unexpectedly found '{pattern}'"
        else:
            passed = False
            evidence = f"Unknown assertion type: {assert_type}"

        results.append({
            "description": desc,
            "passed": passed,
            "evidence": evidence,
            "type": assert_type,
            "pattern": pattern,
        })

    return results


# =============================================================================
# Scenario Runner
# =============================================================================

def run_scenario_cli(
    scenario: dict,
    cli: str = "copilot",
    timeout_response: int = 120,
    verbose: bool = False,
    debug: bool = False,
) -> dict:
    """Run a scenario using non-interactive CLI mode (copilot -p / claude -p).

    Uses -p for each prompt with --resume to maintain session context.
    Parses JSON output for assertions. No tmux needed.

    This is the preferred approach for copilot — avoids TUI issues entirely.
    """
    results = {
        "scenario": scenario["name"],
        "description": scenario.get("description", ""),
        "cli": cli,
        "session": None,
        "steps": [],
        "start_time": time.time(),
    }

    session_id = None
    perm_flag = "--yolo" if cli == "copilot" else "--dangerously-skip-permissions"

    # Validate read-only prompts
    safety_issues = validate_prompts_readonly(scenario["steps"])
    if safety_issues:
        results["error"] = "Unsafe prompts for auto-approve mode"
        results["safety_issues"] = safety_issues
        if verbose:
            for issue in safety_issues:
                console.print(f"  [red]BLOCKED:[/red] {issue}")
        return results

    for step in scenario["steps"]:
        step_name = step.get("name", f"step-{len(results['steps']) + 1}")
        prompt = step["prompt"]
        step_timeout = step.get("timeout", timeout_response)

        if verbose:
            console.print(f"\n[cyan]Step: {step_name}[/cyan]")
            console.print(f"[dim]Prompt: {prompt}[/dim]")

        # Build command
        cmd = [cli, "-p", prompt, perm_flag, "--output-format", "json"]
        if session_id:
            cmd.append(f"--resume={session_id}")

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=step_timeout,
                cwd=str(PLUGIN_ROOT),
            )
            output = proc.stdout
        except subprocess.TimeoutExpired:
            output = ""
            if verbose:
                console.print(f"  [yellow]Timeout ({step_timeout}s)[/yellow]")

        # Parse JSONL output
        assistant_text = ""
        for line in output.split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                etype = event.get("type", "")

                # Capture session ID from result
                if etype == "result":
                    sid = event.get("sessionId")
                    if sid:
                        session_id = sid
                        results["session"] = sid

                # Capture assistant messages
                if etype == "assistant.message":
                    text = event.get("data", {}).get("content", "")
                    if text:
                        assistant_text += text + "\n"

                # Capture tool use (skill invocations, bash commands)
                if etype in ("assistant.tool_use", "tool.output"):
                    tool_text = json.dumps(event.get("data", {}))
                    assistant_text += tool_text + "\n"

            except json.JSONDecodeError:
                # Non-JSON lines (text output mode fallback)
                assistant_text += line + "\n"

        # Check assertions against the full response
        assertion_results = []
        if step.get("assertions"):
            assertion_results = check_assertions(assistant_text, step["assertions"])

        passed = all(a["passed"] for a in assertion_results) if assertion_results else True

        step_result = {
            "name": step_name,
            "prompt": prompt,
            "passed": passed,
            "assertions": assertion_results,
            "output_length": len(assistant_text),
        }

        if verbose:
            for a in assertion_results:
                status = "[green]PASS[/green]" if a["passed"] else "[red]FAIL[/red]"
                console.print(f"  {status} {a['description']}: {a['evidence'][:60]}")

        if debug and assistant_text.strip():
            display = assistant_text.strip()[:2000]
            console.print(Panel(
                display + ("\n..." if len(assistant_text) > 2000 else ""),
                title=f"[dim]response: {step_name}[/dim]",
                border_style="dim",
            ))

        results["steps"].append(step_result)

        # Pause between steps
        pause = step.get("pause_after", 1)
        if pause > 0:
            time.sleep(pause)

    results["end_time"] = time.time()
    results["duration_seconds"] = round(results["end_time"] - results["start_time"], 1)

    total = len(results["steps"])
    passed = sum(1 for s in results["steps"] if s["passed"])
    results["summary"] = {"total_steps": total, "passed": passed, "failed": total - passed}

    return results


def run_scenario(
    scenario: dict,
    cli: str = "copilot",
    timeout_ready: int = 60,
    timeout_response: int = 120,
    verbose: bool = False,
    debug: bool = False,
    skip_permissions: bool = True,
) -> dict:
    """Run a multi-prompt test scenario.

    Scenario format:
    {
        "name": "routing-basic",
        "description": "Test basic routing accuracy",
        "ready_pattern": "\\$|>|❯",
        "steps": [
            {
                "name": "step-1",
                "prompt": "what should I focus on today?",
                "timeout": 60,
                "assertions": [
                    {"pattern": "brain|briefing|goal", "type": "regex", "description": "Routes to default context"}
                ]
            }
        ]
    }
    """
    session_name = f"{SESSION_PREFIX}-{uuid.uuid4().hex[:8]}"
    ready_pattern = scenario.get("ready_pattern", r"\$|>|❯")
    results = {
        "scenario": scenario["name"],
        "description": scenario.get("description", ""),
        "cli": cli,
        "session": session_name,
        "steps": [],
        "start_time": time.time(),
    }

    # Validate prompts are read-only (safety check for --dangerously-skip-permissions)
    if skip_permissions:
        safety_issues = validate_prompts_readonly(scenario["steps"])
        if safety_issues:
            results["error"] = "Unsafe prompts for skip-permissions mode"
            results["safety_issues"] = safety_issues
            if verbose:
                console.print("[red]Safety check failed — prompts contain action verbs:[/red]")
                for issue in safety_issues:
                    console.print(f"  [red]BLOCKED:[/red] {issue}")
            return results

    try:
        # Create session
        if verbose:
            if skip_permissions and cli == "claude":
                console.print(f"[blue]Creating session:[/blue] {session_name} [dim](--dangerously-skip-permissions)[/dim]")
            else:
                console.print(f"[blue]Creating session:[/blue] {session_name}")
        create_session(session_name, cli, str(PLUGIN_ROOT), skip_permissions=skip_permissions)

        # Wait for CLI to be ready
        if verbose:
            console.print(f"[blue]Waiting for {cli} to be ready...[/blue]")
        if not wait_for_ready(session_name, ready_pattern, timeout=timeout_ready, cli=cli):
            results["error"] = f"{cli} did not become ready within {timeout_ready}s"
            return results

        if verbose:
            console.print(f"[green]{cli} is ready[/green]")

        # Run each step
        for step in scenario["steps"]:
            step_name = step.get("name", f"step-{len(results['steps']) + 1}")
            prompt = step["prompt"]
            step_timeout = step.get("timeout", timeout_response)

            if verbose:
                console.print(f"\n[cyan]Step: {step_name}[/cyan]")
                console.print(f"[dim]Prompt: {prompt}[/dim]")

            # Capture state before sending prompt
            before = capture_pane(session_name)

            # Send the prompt
            send_prompt(session_name, prompt, cli=cli)

            # Wait for response
            after = wait_for_response(
                session_name,
                ready_pattern,
                before,
                timeout=step_timeout,
            )

            # Extract new output (what appeared after our prompt)
            new_output = after[len(before):] if after.startswith(before[:100]) else after

            # Check assertions
            assertion_results = []
            if step.get("assertions"):
                assertion_results = check_assertions(after, step["assertions"])

            passed = all(a["passed"] for a in assertion_results) if assertion_results else True

            step_result = {
                "name": step_name,
                "prompt": prompt,
                "passed": passed,
                "assertions": assertion_results,
                "output_length": len(new_output),
            }

            if verbose:
                for a in assertion_results:
                    status = "[green]PASS[/green]" if a["passed"] else "[red]FAIL[/red]"
                    console.print(f"  {status} {a['description']}: {a['evidence'][:60]}")

            # Show tmux pane content in debug mode
            if debug:
                # Capture the full visible pane (not just the diff)
                full_pane = capture_pane(session_name, history=200)
                # Strip leading/trailing blank lines
                pane_lines = [l for l in full_pane.split("\n") if l.strip()]
                display_output = "\n".join(pane_lines[-40:])  # last 40 non-empty lines
                if display_output:
                    console.print(Panel(
                        display_output[:3000] + ("\n..." if len(display_output) > 3000 else ""),
                        title=f"[dim]tmux pane: {step_name}[/dim]",
                        border_style="dim",
                    ))

            # Save full output when debug is on or explicitly requested
            if debug or step.get("capture_output", False):
                step_result["output"] = new_output

            results["steps"].append(step_result)

            # Wait between steps if specified
            pause = step.get("pause_after", 2)
            if pause > 0:
                time.sleep(pause)

    except Exception as e:
        results["error"] = str(e)
    finally:
        # Always clean up
        results["end_time"] = time.time()
        results["duration_seconds"] = round(results["end_time"] - results["start_time"], 1)
        kill_session(session_name)

    # Summary
    total = len(results["steps"])
    passed = sum(1 for s in results["steps"] if s["passed"])
    results["summary"] = {
        "total_steps": total,
        "passed": passed,
        "failed": total - passed,
    }

    return results


# =============================================================================
# Display
# =============================================================================

def display_results(results: dict):
    """Display scenario results."""
    summary = results.get("summary", {})

    if "error" in results:
        console.print(Panel(
            f"[red]Error:[/red] {results['error']}",
            title=results["scenario"],
        ))
        return

    table = Table(title=f"Scenario: {results['scenario']}")
    table.add_column("Step", style="cyan")
    table.add_column("Prompt", max_width=50)
    table.add_column("Status", justify="center")
    table.add_column("Assertions", justify="center")

    for step in results["steps"]:
        status = "[green]PASS[/green]" if step["passed"] else "[red]FAIL[/red]"
        assertion_count = len(step.get("assertions", []))
        passed_count = sum(1 for a in step.get("assertions", []) if a["passed"])
        table.add_row(
            step["name"],
            step["prompt"][:50],
            status,
            f"{passed_count}/{assertion_count}" if assertion_count else "-",
        )

    console.print(table)

    # Show failures in detail
    for step in results["steps"]:
        failed = [a for a in step.get("assertions", []) if not a["passed"]]
        if failed:
            console.print(f"\n[red]{step['name']} failures:[/red]")
            for a in failed:
                console.print(f"  [red]FAIL:[/red] {a['description']}")
                console.print(f"        {a['evidence']}")

    console.print(
        f"\n[bold]Result:[/bold] {summary['passed']}/{summary['total_steps']} steps passed "
        f"({results.get('duration_seconds', '?')}s, cli={results['cli']})"
    )


# =============================================================================
# Main
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Multi-prompt session testing via tmux")
    parser.add_argument("--scenario", required=True, help="Path to scenario JSON file")
    parser.add_argument("--cli", default="copilot", choices=["copilot", "claude"], help="CLI to test")
    parser.add_argument("--timeout-ready", type=int, default=60, help="Seconds to wait for CLI startup")
    parser.add_argument("--timeout-response", type=int, default=120, help="Seconds to wait per response")
    parser.add_argument("--dry-run", action="store_true", help="Show scenario without running")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--debug", action="store_true", help="Show tmux pane captures for each step")
    parser.add_argument("--save-output", help="Save full results JSON to this path")
    args = parser.parse_args()

    # Debug implies verbose
    if args.debug:
        args.verbose = True

    # Load scenario
    scenario_path = Path(args.scenario)
    if not scenario_path.exists():
        console.print(f"[red]Error:[/red] {scenario_path} not found")
        raise SystemExit(1)

    scenario = json.loads(scenario_path.read_text())

    if args.dry_run:
        console.print(Panel(
            f"[bold]{scenario['name']}[/bold]\n"
            f"{scenario.get('description', '')}\n\n"
            f"CLI: {args.cli}\n"
            f"Steps: {len(scenario['steps'])}",
            title="Scenario (dry run)",
        ))
        for i, step in enumerate(scenario["steps"], 1):
            assertions = len(step.get("assertions", []))
            console.print(f"  {i}. [cyan]{step.get('name', f'step-{i}')}[/cyan]: {step['prompt'][:60]}")
            if assertions:
                console.print(f"     {assertions} assertion(s)")
        raise SystemExit(0)

    # Route to the right runner based on CLI
    if args.cli == "copilot":
        # Copilot: use non-interactive -p mode (avoids TUI issues)
        results = run_scenario_cli(
            scenario=scenario,
            cli=args.cli,
            timeout_response=args.timeout_response,
            verbose=args.verbose,
            debug=args.debug,
        )
    else:
        # Claude: use tmux interactive session
        try:
            subprocess.run(["tmux", "-V"], capture_output=True, timeout=5, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            console.print("[red]Error:[/red] tmux not found")
            raise SystemExit(1)

        results = run_scenario(
            scenario=scenario,
            cli=args.cli,
            timeout_ready=args.timeout_ready,
            timeout_response=args.timeout_response,
            verbose=args.verbose,
            debug=args.debug,
        )

    if args.json:
        console.print_json(json.dumps(results, indent=2, default=str))
    else:
        display_results(results)

    if args.save_output:
        Path(args.save_output).write_text(json.dumps(results, indent=2, default=str))
        console.print(f"\n[dim]Results saved to {args.save_output}[/dim]")

    all_passed = results.get("summary", {}).get("failed", 1) == 0
    raise SystemExit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
