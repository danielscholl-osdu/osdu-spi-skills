---
title: Contributing
description: How to contribute to OSDU SPI Skills
---

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- `tmux` (for L3/L4 session tests)
- GitHub Copilot CLI and/or Claude Code (for live tests)

## Quick Start

```bash
git clone https://github.com/danielscholl-osdu/osdu-spi-skills.git
cd osdu-spi-skills

# Run fast tests (no AI calls)
make test

# Run live trigger tests
make test-triggers CLI=copilot
make test-triggers CLI=claude
```

## Development Workflow

```bash
# 1. After every change — fast feedback
make test                     # L0 + L1 + L2 + pytest (~15 seconds)

# 2. Before pushing — verify triggers
make test-triggers CLI=copilot  # L3 (~2 minutes)

# 3. For workflow changes — session tests
make test-sessions CLI=claude S=brain  # L4 for one skill

# 4. For skill value changes — benchmark
make test-benchmark S=brain   # L5 comparison
```

## Key Conventions

### Do

- Keep skill descriptions under 500 characters
- Include both positive and negative trigger evals (8+ each)
- Use `allowed-tools` frontmatter for Claude tool restrictions
- Use lowercase kebab-case for skill names
- Reference the `setup` skill when tools are missing
- Test against both Copilot and Claude before merging

### Don't

- Don't add `allowed-tools` unless the skill genuinely needs tool restrictions
- Don't create skills that overlap with existing ones
- Don't hard-code paths — use `$OSDU_WORKSPACE` and `$OSDU_BRAIN`
- Don't add AI attribution to commit messages (no Co-Authored-By)

## Project Layout

```
osdu-spi-skills/
├── plugin.json            # APM manifest
├── AGENTS.md              # Copilot routing table
├── CLAUDE.md              # Claude routing table
├── agents/                # 8 agent definitions
├── skills/                # 28 skill directories
│   └── <skill>/
│       ├── SKILL.md       # Required
│       ├── references/    # Optional supporting docs
│       ├── scripts/       # Optional executable code
│       └── scaffold/      # Optional templates
├── commands/              # 4 slash commands
├── reference/             # Shared reference docs
├── tests/
│   ├── scripts/           # Test framework (in-house)
│   ├── evals/triggers/    # Trigger accuracy tests
│   ├── evals/scenarios/   # Multi-turn workflow tests
│   ├── unit/              # Pytest unit tests
│   └── benchmarks/        # Skill value comparison results
├── docs/                  # Astro Starlight documentation site
├── Makefile               # Test runner
└── pyproject.toml         # Python config
```
