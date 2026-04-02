# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pytest",
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
Tests for the plugin validator.

Validates that the validator itself works correctly, and that the current
plugin passes all checks. Run with:

    uv run pytest tests/unit/test_validate.py -v
"""

import json
import sys
from pathlib import Path

import pytest

# Add scripts dir to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from validate import (
    parse_frontmatter,
    validate_plugin_json,
    validate_agents_md,
    validate_agent_file,
    validate_skill,
    validate_cross_references,
    validate_orphans,
    run_full_validation,
    PLUGIN_ROOT,
)


# =============================================================================
# Frontmatter Parser Tests
# =============================================================================

class TestParseFrontmatter:
    def test_simple_frontmatter(self):
        content = "---\nname: test\ndescription: A test\n---\nBody here"
        fm, body = parse_frontmatter(content)
        assert fm is not None
        assert fm["name"] == "test"
        assert fm["description"] == "A test"
        assert "Body here" in body

    def test_no_frontmatter(self):
        content = "# Just a heading\n\nSome content"
        fm, body = parse_frontmatter(content)
        assert fm is None

    def test_multiline_description(self):
        content = "---\nname: test\ndescription: |\n  Line one\n  Line two\n---\nBody"
        fm, body = parse_frontmatter(content)
        assert fm is not None
        assert "Line one" in fm["description"]
        assert "Line two" in fm["description"]

    def test_quoted_values(self):
        content = '---\nname: "my-skill"\ndescription: \'A skill\'\n---\nBody'
        fm, body = parse_frontmatter(content)
        assert fm["name"] == "my-skill"
        assert fm["description"] == "A skill"

    def test_empty_body(self):
        content = "---\nname: test\n---\n"
        fm, body = parse_frontmatter(content)
        assert fm is not None
        assert body == ""


# =============================================================================
# Plugin Structure Tests (against live plugin)
# =============================================================================

class TestPluginJson:
    def test_exists(self):
        assert (PLUGIN_ROOT / "plugin.json").exists()

    def test_valid_json(self):
        data = json.loads((PLUGIN_ROOT / "plugin.json").read_text(encoding="utf-8"))
        assert isinstance(data, dict)

    def test_required_fields(self):
        data = json.loads((PLUGIN_ROOT / "plugin.json").read_text(encoding="utf-8"))
        assert data.get("name")
        assert data.get("description")
        assert data.get("version")

    def test_version_semver(self):
        data = json.loads((PLUGIN_ROOT / "plugin.json").read_text(encoding="utf-8"))
        import re
        assert re.match(r"^\d+\.\d+\.\d+", data["version"])

    def test_paths_exist(self):
        data = json.loads((PLUGIN_ROOT / "plugin.json").read_text(encoding="utf-8"))
        if data.get("agents"):
            assert (PLUGIN_ROOT / data["agents"]).is_dir()
        if data.get("skills"):
            assert (PLUGIN_ROOT / data["skills"]).is_dir()

    def test_passes_validation(self):
        result = validate_plugin_json(PLUGIN_ROOT)
        assert result.passed, f"Errors: {result.errors}"


class TestAgentsMd:
    def test_exists(self):
        assert (PLUGIN_ROOT / "AGENTS.md").exists()

    def test_has_content(self):
        content = (PLUGIN_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        assert len(content) > 100

    def test_passes_validation(self):
        result = validate_agents_md(PLUGIN_ROOT)
        assert result.passed, f"Errors: {result.errors}"


# =============================================================================
# Agent File Tests
# =============================================================================

class TestAgentFiles:
    @pytest.fixture
    def agent_files(self):
        agents_dir = PLUGIN_ROOT / "agents"
        # Support both .agent.md (Copilot convention) and .md (APM convention)
        files = sorted(agents_dir.glob("*.agent.md"))
        if not files:
            files = sorted(agents_dir.glob("*.md"))
        return files

    def test_agents_exist(self, agent_files):
        assert len(agent_files) > 0, "No agent files found"

    def test_all_have_frontmatter(self, agent_files):
        for f in agent_files:
            content = f.read_text(encoding="utf-8")
            fm, _ = parse_frontmatter(content)
            assert fm is not None, f"{f.name} missing frontmatter"

    def test_all_have_name(self, agent_files):
        for f in agent_files:
            fm, _ = parse_frontmatter(f.read_text(encoding="utf-8"))
            assert fm.get("name"), f"{f.name} missing 'name' field"

    def test_all_have_description(self, agent_files):
        for f in agent_files:
            fm, _ = parse_frontmatter(f.read_text(encoding="utf-8"))
            assert fm.get("description"), f"{f.name} missing 'description' field"

    def test_names_are_lowercase(self, agent_files):
        for f in agent_files:
            fm, _ = parse_frontmatter(f.read_text(encoding="utf-8"))
            name = fm.get("name", "")
            assert name == name.lower(), (
                f"{f.name}: name '{name}' must be lowercase"
            )

    def test_names_match_filenames(self, agent_files):
        for f in agent_files:
            fm, _ = parse_frontmatter(f.read_text(encoding="utf-8"))
            name = fm.get("name", "")
            # Accept both .agent.md (Copilot) and .md (APM) conventions
            valid_names = {f"{name}.agent.md", f"{name}.md"}
            assert f.name in valid_names, (
                f"Filename '{f.name}' doesn't match name '{name}' "
                f"(expected one of {valid_names})"
            )

    def test_no_duplicate_names(self, agent_files):
        names = []
        for f in agent_files:
            fm, _ = parse_frontmatter(f.read_text(encoding="utf-8"))
            names.append(fm.get("name", ""))
        assert len(names) == len(set(names)), f"Duplicate agent names: {names}"

    def test_all_pass_validation(self, agent_files):
        for f in agent_files:
            result = validate_agent_file(f)
            assert result.passed, f"{f.name} failed: {result.errors}"


# =============================================================================
# Skill Tests
# =============================================================================

class TestSkills:
    @pytest.fixture
    def skill_dirs(self):
        skills_dir = PLUGIN_ROOT / "skills"
        return sorted(
            d for d in skills_dir.iterdir()
            if d.is_dir() and (d / "SKILL.md").exists()
        )

    def test_skills_exist(self, skill_dirs):
        assert len(skill_dirs) > 0, "No skills found"

    def test_all_have_frontmatter(self, skill_dirs):
        for d in skill_dirs:
            content = (d / "SKILL.md").read_text(encoding="utf-8")
            fm, _ = parse_frontmatter(content)
            assert fm is not None, f"{d.name}/SKILL.md missing frontmatter"

    def test_all_have_name(self, skill_dirs):
        for d in skill_dirs:
            fm, _ = parse_frontmatter((d / "SKILL.md").read_text(encoding="utf-8"))
            assert fm.get("name"), f"{d.name}/SKILL.md missing 'name'"

    def test_all_have_description(self, skill_dirs):
        for d in skill_dirs:
            fm, _ = parse_frontmatter((d / "SKILL.md").read_text(encoding="utf-8"))
            assert fm.get("description"), f"{d.name}/SKILL.md missing 'description'"

    def test_names_are_lowercase_kebab(self, skill_dirs):
        import re
        for d in skill_dirs:
            fm, _ = parse_frontmatter((d / "SKILL.md").read_text(encoding="utf-8"))
            name = fm.get("name", "")
            assert re.match(r"^[a-z][a-z0-9-]*$", name), (
                f"{d.name}: name '{name}' must be lowercase kebab-case"
            )

    def test_names_match_directories(self, skill_dirs):
        for d in skill_dirs:
            fm, _ = parse_frontmatter((d / "SKILL.md").read_text(encoding="utf-8"))
            name = fm.get("name", "")
            assert d.name == name, (
                f"Directory '{d.name}' doesn't match skill name '{name}'"
            )

    def test_no_duplicate_names(self, skill_dirs):
        names = []
        for d in skill_dirs:
            fm, _ = parse_frontmatter((d / "SKILL.md").read_text(encoding="utf-8"))
            names.append(fm.get("name", ""))
        assert len(names) == len(set(names)), f"Duplicate skill names found"

    def test_all_pass_validation(self, skill_dirs):
        for d in skill_dirs:
            result = validate_skill(d)
            assert result.passed, f"{d.name} failed: {result.errors}"


# =============================================================================
# Setup Delegation Tests
# =============================================================================

class TestSetupDelegation:
    """Skills with --version pre-flight checks must delegate to setup on failure."""

    def test_version_checks_have_setup_delegation(self):
        """Every skill with a pre-flight version check in Quick Start should
        tell the agent to stop and use the setup skill if the tool is missing."""
        import re
        skills_dir = PLUGIN_ROOT / "skills"
        missing_delegation = []
        # Pattern: a bash block containing a tool --version check
        # (not a CLI flag like --version "5.3.0")
        preflight_pattern = re.compile(
            r"```bash\n\s*\S+\s+--version"
        )
        for skill_dir in sorted(skills_dir.iterdir()):
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue
            content = skill_md.read_text(encoding="utf-8")
            if skill_dir.name == "setup":
                continue
            if preflight_pattern.search(content):
                if "setup skill" not in content.lower():
                    missing_delegation.append(skill_dir.name)
        assert not missing_delegation, (
            f"Skills with pre-flight --version checks but no setup skill delegation: "
            f"{missing_delegation}. Add: 'stop and use the `setup` skill' instruction."
        )


# =============================================================================
# Cross-Reference Tests
# =============================================================================

class TestCrossReferences:
    def test_passes_validation(self):
        result = validate_cross_references(PLUGIN_ROOT)
        assert result.passed, f"Errors: {result.errors}"

    def test_no_orphan_files(self):
        result = validate_orphans(PLUGIN_ROOT)
        assert result.passed, f"Errors: {result.errors}"
        # Orphan warnings are OK but flag them
        if result.warnings:
            pytest.skip(f"Orphan warnings: {result.warnings}")


# =============================================================================
# Full Validation
# =============================================================================

class TestFullValidation:
    def test_full_plugin_passes(self):
        results = run_full_validation(PLUGIN_ROOT)
        errors = []
        for r in results:
            for e in r.errors:
                errors.append(f"{r.target}: {e}")
        assert not errors, f"Plugin validation failed:\n" + "\n".join(errors)
