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
Copilot CLI Plugin Validator

Validates plugin structure, agents, skills, MCP config, and cross-references
against the GitHub Copilot CLI plugin specification.

Usage:
    uv run tests/scripts/validate.py                # validate entire plugin
    uv run tests/scripts/validate.py --json          # JSON output
    uv run tests/scripts/validate.py agents/         # validate just agents
    uv run tests/scripts/validate.py skills/brain/   # validate one skill
"""

import json
import re
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

# Resolve plugin root (walk up from script location)
# tests/scripts/ → 2 levels up to repo root
SCRIPT_DIR = Path(__file__).parent
PLUGIN_ROOT = SCRIPT_DIR.parent.parent


# =============================================================================
# Frontmatter Parser (no PyYAML dependency)
# =============================================================================

def parse_frontmatter(content: str) -> tuple[dict | None, str]:
    """Extract YAML frontmatter from markdown content.

    Handles simple key: value pairs and multiline values using | or >.
    Does NOT handle nested objects or lists — use full YAML parser for that.
    """
    if not content.startswith("---"):
        return None, content

    end = content.find("\n---", 3)
    if end == -1:
        return None, content

    frontmatter_text = content[3:end].strip()
    body = content[end + 4:].strip()

    fm: dict[str, str] = {}
    current_key = None
    current_value_lines: list[str] = []
    is_block_scalar = False

    for line in frontmatter_text.split("\n"):
        stripped = line.strip()

        # Skip comments and empty lines in non-block context
        if not is_block_scalar and (not stripped or stripped.startswith("#")):
            continue

        # Check for new key: value pair (not indented)
        if not line.startswith(" ") and not line.startswith("\t") and ":" in line:
            # Save previous key
            if current_key is not None:
                fm[current_key] = "\n".join(current_value_lines).strip()

            key, _, value = line.partition(":")
            current_key = key.strip()
            value = value.strip().strip("'\"")

            if value in ("|", ">", ">-"):
                is_block_scalar = True
                current_value_lines = []
            else:
                is_block_scalar = False
                current_value_lines = [value]
        elif is_block_scalar and current_key:
            current_value_lines.append(line.strip())
        elif current_key and is_block_scalar:
            current_value_lines.append(stripped)

    # Save last key
    if current_key is not None:
        fm[current_key] = "\n".join(current_value_lines).strip()

    return fm, body


# =============================================================================
# Validation Result
# =============================================================================

class ValidationResult:
    """Collects errors and warnings for a single validation target."""

    def __init__(self, target: str):
        self.target = target
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str):
        self.errors.append(msg)

    def warn(self, msg: str):
        self.warnings.append(msg)

    @property
    def passed(self) -> bool:
        return len(self.errors) == 0

    def to_dict(self) -> dict:
        return {
            "target": self.target,
            "passed": self.passed,
            "errors": self.errors,
            "warnings": self.warnings,
        }


def read_utf8_text(path: Path, result: ValidationResult | None = None) -> str | None:
    """Read text file as UTF-8 with structured error reporting."""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        if result is not None:
            try:
                display_path = str(path.relative_to(PLUGIN_ROOT))
            except ValueError:
                display_path = str(path)
            result.error(f"Failed to decode '{display_path}' as UTF-8: {e}")
        return None
    except OSError as e:
        if result is not None:
            try:
                display_path = str(path.relative_to(PLUGIN_ROOT))
            except ValueError:
                display_path = str(path)
            result.error(f"Failed to read '{display_path}': {e}")
        return None


# =============================================================================
# Validators
# =============================================================================

def validate_plugin_json(root: Path) -> ValidationResult:
    """Validate plugin.json manifest."""
    result = ValidationResult("plugin.json")
    path = root / "plugin.json"

    if not path.exists():
        result.error("plugin.json not found at plugin root")
        return result

    content = read_utf8_text(path, result)
    if content is None:
        return result

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        result.error(f"Invalid JSON: {e}")
        return result

    # Required fields
    required = ["name", "description", "version"]
    for field in required:
        if field not in data:
            result.error(f"Missing required field: {field}")
        elif not isinstance(data[field], str) or not data[field].strip():
            result.error(f"Field '{field}' must be a non-empty string")

    # Version format
    version = data.get("version", "")
    if version and not re.match(r"^\d+\.\d+\.\d+", version):
        result.error(f"Version '{version}' must follow semver (X.Y.Z)")

    # Path references
    agents_path = data.get("agents")
    if agents_path:
        if not (root / agents_path).is_dir():
            result.error(f"Agents path '{agents_path}' does not exist")
    else:
        result.warn("No 'agents' path declared")

    skills_path = data.get("skills")
    if skills_path:
        if not (root / skills_path).is_dir():
            result.error(f"Skills path '{skills_path}' does not exist")
    else:
        result.warn("No 'skills' path declared")

    mcp_servers = data.get("mcpServers")
    if mcp_servers:
        if isinstance(mcp_servers, str):
            # Path reference to .mcp.json file
            if not (root / mcp_servers).is_file():
                result.error(f"MCP servers path '{mcp_servers}' does not exist")
        elif isinstance(mcp_servers, dict):
            # Inline MCP server definitions — validate each has command or url
            for name, config in mcp_servers.items():
                if not isinstance(config, dict):
                    result.error(f"MCP server '{name}' must be an object")
                elif not config.get("command") and not config.get("url"):
                    result.error(f"MCP server '{name}' needs 'command' or 'url'")

    # Author
    author = data.get("author")
    if not author:
        result.warn("No 'author' field")
    elif isinstance(author, dict) and not author.get("name"):
        result.warn("Author object missing 'name'")

    # License
    if not data.get("license"):
        result.warn("No 'license' field")

    return result


def validate_mcp_json(root: Path) -> ValidationResult:
    """Validate .mcp.json MCP server configuration."""
    result = ValidationResult(".mcp.json")
    path = root / ".mcp.json"

    if not path.exists():
        result.warn(".mcp.json not found (optional)")
        return result

    content = read_utf8_text(path, result)
    if content is None:
        return result

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        result.error(f"Invalid JSON: {e}")
        return result

    servers = data.get("mcpServers", {})
    if not servers:
        result.warn("No MCP servers defined")
        return result

    for name, config in servers.items():
        # Must have command or url
        has_command = "command" in config
        has_url = "url" in config

        if not has_command and not has_url:
            result.error(f"Server '{name}': must have 'command' or 'url'")

        if has_command:
            if not isinstance(config["command"], str):
                result.error(f"Server '{name}': 'command' must be a string")
            args = config.get("args", [])
            if not isinstance(args, list):
                result.error(f"Server '{name}': 'args' must be an array")

            # Check if extension files exist for local servers
            if args and any("extensions/" in str(a) for a in args):
                ext_path = next(
                    (a for a in args if "extensions/" in str(a)), None
                )
                if ext_path and not (root / ext_path).exists():
                    result.error(
                        f"Server '{name}': extension file '{ext_path}' not found"
                    )

    return result


def validate_agents_md(root: Path) -> ValidationResult:
    """Validate AGENTS.md primary instructions file."""
    result = ValidationResult("AGENTS.md")
    path = root / "AGENTS.md"

    if not path.exists():
        result.error("AGENTS.md not found at plugin root")
        return result

    content = read_utf8_text(path, result)
    if content is None:
        return result
    if len(content.strip()) < 100:
        result.warn("AGENTS.md is very short — should contain project context")

    return result


def validate_agent_file(path: Path) -> ValidationResult:
    """Validate a single agent .agent.md file."""
    result = ValidationResult(str(path.relative_to(PLUGIN_ROOT)))
    content = read_utf8_text(path, result)
    if content is None:
        return result
    fm, body = parse_frontmatter(content)

    # Must have frontmatter
    if fm is None:
        result.error("Missing YAML frontmatter (---)")
        return result

    # Required fields
    name = fm.get("name", "").strip()
    description = fm.get("description", "").strip()

    if not name:
        result.error("Missing required field: name")
    else:
        # Naming convention: lowercase with hyphens
        if name != name.lower():
            result.error(f"Agent name '{name}' must be lowercase")
        if " " in name:
            result.error(f"Agent name '{name}' must not contain spaces (use hyphens)")
        if not re.match(r"^[a-z][a-z0-9-]*$", name):
            result.error(f"Agent name '{name}' must be lowercase alphanumeric with hyphens")

        # Name should match filename
        expected_filename = f"{name}.agent.md"
        if path.name != expected_filename:
            result.warn(
                f"Filename '{path.name}' doesn't match frontmatter name "
                f"(expected '{expected_filename}')"
            )

    if not description:
        result.error("Missing required field: description")
    elif len(description) > 500:
        result.warn(f"Description is {len(description)} chars (consider shortening)")

    # Body content
    if not body or len(body) < 50:
        result.warn("Agent body is very short — should describe capabilities and scope")

    return result


def validate_skill(skill_dir: Path) -> ValidationResult:
    """Validate a skill directory."""
    result = ValidationResult(str(skill_dir.relative_to(PLUGIN_ROOT)))
    skill_md = skill_dir / "SKILL.md"

    if not skill_md.exists():
        result.error("Missing SKILL.md")
        return result

    content = read_utf8_text(skill_md, result)
    if content is None:
        return result
    fm, body = parse_frontmatter(content)

    # Must have frontmatter
    if fm is None:
        result.error("Missing YAML frontmatter (---)")
        return result

    # Required fields
    name = fm.get("name", "").strip()
    description = fm.get("description", "").strip()

    if not name:
        result.error("Missing required field: name")
    else:
        # Naming convention: lowercase with hyphens
        if not re.match(r"^[a-z][a-z0-9-]*$", name):
            result.error(f"Skill name '{name}' must be lowercase alphanumeric with hyphens")
        if len(name) > 64:
            result.error(f"Skill name '{name}' exceeds 64 character limit")

        # Name should match directory name
        if skill_dir.name != name:
            result.warn(
                f"Directory name '{skill_dir.name}' doesn't match "
                f"frontmatter name '{name}'"
            )

    if not description:
        result.error("Missing required field: description")
    elif len(description) < 20:
        result.warn("Description is very short — should explain what AND when to use")
    elif len(description) > 1024:
        result.warn(f"Description is {len(description)} chars (may be truncated)")

    # Body content
    if not body or len(body) < 50:
        result.warn("Skill body is very short — should contain instructions")

    # Check for non-standard frontmatter fields
    standard_fields = {"name", "description", "license"}
    for key in fm:
        if key not in standard_fields:
            result.warn(
                f"Non-standard frontmatter field: '{key}' "
                f"(only name, description, license are in the spec)"
            )

    # Check for references to THIS skill's own scripts/ directory
    # Only flag if the skill references its own scripts (not other skills' scripts
    # or generic "scripts/" mentions in prose)
    own_scripts_pattern = re.compile(
        rf"(?:skills/{re.escape(skill_dir.name)}/scripts/|^scripts/)",
        re.MULTILINE,
    )
    if own_scripts_pattern.search(content):
        scripts_dir = skill_dir / "scripts"
        if not scripts_dir.is_dir():
            result.error(
                f"SKILL.md references {skill_dir.name}/scripts/ "
                f"but directory doesn't exist"
            )

    # Check for references to THIS skill's own reference/ directory
    own_ref_pattern = re.compile(
        rf"(?:skills/{re.escape(skill_dir.name)}/references?/|"
        rf"\breferences?/[a-z])",
        re.MULTILINE,
    )
    if own_ref_pattern.search(content):
        ref_dir = skill_dir / "reference"
        refs_dir = skill_dir / "references"
        if not ref_dir.is_dir() and not refs_dir.is_dir():
            result.warn("SKILL.md references reference docs but directory doesn't exist")

    return result


def validate_cross_references(root: Path) -> ValidationResult:
    """Validate cross-references between plugin components."""
    result = ValidationResult("cross-references")

    # Collect all agent names
    agent_names = set()
    agents_dir = root / "agents"
    if agents_dir.is_dir():
        for f in agents_dir.glob("*.agent.md"):
            content = read_utf8_text(f, result)
            if content is None:
                continue
            fm, _ = parse_frontmatter(content)
            if fm and fm.get("name"):
                agent_names.add(fm["name"].strip())

    # Collect all skill names
    skill_names = set()
    skills_dir = root / "skills"
    if skills_dir.is_dir():
        for d in sorted(skills_dir.iterdir()):
            skill_md = d / "SKILL.md"
            if skill_md.exists():
                content = read_utf8_text(skill_md, result)
                if content is None:
                    continue
                fm, _ = parse_frontmatter(content)
                if fm and fm.get("name"):
                    skill_names.add(fm["name"].strip())

    # Check AGENTS.md references
    agents_md = root / "AGENTS.md"
    if agents_md.exists():
        routing_content = read_utf8_text(agents_md, result)
        if routing_content is None:
            return result

        # Check agents are mentioned in project context
        for name in agent_names:
            if name not in routing_content and f"@{name}" not in routing_content:
                result.warn(f"Agent '{name}' not referenced in AGENTS.md")

        # Check skills are mentioned in project context
        for name in skill_names:
            if name not in routing_content:
                result.warn(f"Skill '{name}' not referenced in AGENTS.md")

    # Check for duplicate names across agents and skills
    overlap = agent_names & skill_names
    if overlap:
        for name in overlap:
            result.warn(f"Name '{name}' used by both an agent and a skill")

    # Check agent files reference valid skills
    if agents_dir.is_dir():
        for f in agents_dir.glob("*.agent.md"):
            content = read_utf8_text(f, result)
            if content is None:
                continue
            # Look for skill references in agent content
            for match in re.finditer(r"skills/([a-z0-9-]+)", content):
                ref_skill = match.group(1)
                if ref_skill not in skill_names and not (skills_dir / ref_skill).is_dir():
                    result.error(
                        f"Agent '{f.name}' references skill '{ref_skill}' "
                        f"which doesn't exist"
                    )

    return result


def validate_orphans(root: Path) -> ValidationResult:
    """Detect files that exist but aren't reachable from plugin.json."""
    result = ValidationResult("orphan-detection")

    # Check for common orphan patterns
    for pattern, description in [
        ("SOUL.md", "Unreferenced SOUL.md (should be AGENTS.md)"),
        ("routing.md", "Unreferenced routing.md (should be in AGENTS.md)"),
        ("CLAUDE.md", "CLAUDE.md found (not used by Copilot CLI plugins)"),
        (".github/copilot-instructions.md", "copilot-instructions.md (valid but unused by plugins)"),
    ]:
        if (root / pattern).exists():
            result.warn(description)

    # Check for skill directories without SKILL.md
    skills_dir = root / "skills"
    if skills_dir.is_dir():
        for d in sorted(skills_dir.iterdir()):
            if d.is_dir() and not (d / "SKILL.md").exists():
                # Allow shared resource directories
                if d.name not in ("osdu-shared",):
                    result.warn(f"Directory skills/{d.name}/ has no SKILL.md")

    return result


# =============================================================================
# Runner
# =============================================================================

def run_full_validation(root: Path) -> list[ValidationResult]:
    """Run all validators on the plugin."""
    results = []

    results.append(validate_plugin_json(root))
    results.append(validate_mcp_json(root))
    results.append(validate_agents_md(root))

    # Agents
    agents_dir = root / "agents"
    if agents_dir.is_dir():
        for f in sorted(agents_dir.glob("*.agent.md")):
            results.append(validate_agent_file(f))

    # Skills
    skills_dir = root / "skills"
    if skills_dir.is_dir():
        for d in sorted(skills_dir.iterdir()):
            if d.is_dir() and (d / "SKILL.md").exists():
                results.append(validate_skill(d))

    results.append(validate_cross_references(root))
    results.append(validate_orphans(root))

    return results


def run_targeted_validation(target: Path) -> list[ValidationResult]:
    """Run validation on a specific file or directory."""
    results = []

    if target.is_file():
        if target.name.endswith(".agent.md"):
            results.append(validate_agent_file(target))
        elif target.name == "SKILL.md":
            results.append(validate_skill(target.parent))
        elif target.name == "plugin.json":
            results.append(validate_plugin_json(target.parent))
        elif target.name == ".mcp.json":
            results.append(validate_mcp_json(target.parent))
        elif target.name == "AGENTS.md":
            results.append(validate_agents_md(target.parent))
    elif target.is_dir():
        # Check if it's an agents directory
        agent_files = list(target.glob("*.agent.md"))
        if agent_files:
            for f in sorted(agent_files):
                results.append(validate_agent_file(f))
        # Check if it's a skill directory
        elif (target / "SKILL.md").exists():
            results.append(validate_skill(target))
        # Check if it's the skills root
        else:
            for d in sorted(target.iterdir()):
                if d.is_dir() and (d / "SKILL.md").exists():
                    results.append(validate_skill(d))

    return results


def display_results(results: list[ValidationResult], output_json: bool = False):
    """Display validation results."""
    if output_json:
        output = {
            "passed": all(r.passed for r in results),
            "total": len(results),
            "errors": sum(len(r.errors) for r in results),
            "warnings": sum(len(r.warnings) for r in results),
            "results": [r.to_dict() for r in results],
        }
        console.print_json(json.dumps(output))
        return

    # Summary table
    table = Table(title="Plugin Validation Results")
    table.add_column("Target", style="cyan", max_width=40)
    table.add_column("Status", justify="center")
    table.add_column("Errors", justify="right", style="red")
    table.add_column("Warnings", justify="right", style="yellow")

    for r in results:
        status = "[green]PASS[/green]" if r.passed else "[red]FAIL[/red]"
        table.add_row(r.target, status, str(len(r.errors)), str(len(r.warnings)))

    console.print(table)

    # Detail section for errors and warnings
    has_issues = any(r.errors or r.warnings for r in results)
    if has_issues:
        console.print()
        for r in results:
            if r.errors or r.warnings:
                status_color = "red" if r.errors else "yellow"
                console.print(f"[bold {status_color}]{r.target}[/bold {status_color}]")
                for e in r.errors:
                    console.print(f"  [red]ERROR:[/red] {e}")
                for w in r.warnings:
                    console.print(f"  [yellow]WARN:[/yellow]  {w}")
                console.print()

    # Summary line
    total_errors = sum(len(r.errors) for r in results)
    total_warnings = sum(len(r.warnings) for r in results)
    passed = all(r.passed for r in results)

    if passed and total_warnings == 0:
        console.print("[bold green]All checks passed.[/bold green]")
    elif passed:
        console.print(
            f"[bold green]All checks passed[/bold green] "
            f"with [yellow]{total_warnings} warning(s)[/yellow]."
        )
    else:
        console.print(
            f"[bold red]{total_errors} error(s)[/bold red], "
            f"[yellow]{total_warnings} warning(s)[/yellow]."
        )

    return passed


def main():
    """Entry point."""
    args = sys.argv[1:]
    output_json = "--json" in args
    args = [a for a in args if a != "--json"]

    if args:
        target = Path(args[0]).resolve()
        if not target.exists():
            console.print(f"[red]Error:[/red] {target} does not exist")
            raise SystemExit(1)
        results = run_targeted_validation(target)
    else:
        results = run_full_validation(PLUGIN_ROOT)

    passed = display_results(results, output_json)
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
