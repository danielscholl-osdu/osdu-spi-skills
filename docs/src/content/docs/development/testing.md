---
title: Testing
description: Six-layer test framework for cross-platform validation
---

## Why AI Plugins Need Different Testing

AI plugins are **probabilistic, not deterministic**. A skill description change can silently steal triggers from another skill. A routing table edit can break multi-turn conversations. Traditional unit tests don't catch these problems.

The test framework validates at six levels, from fast structural checks to slow AI-powered integration tests.

## Test Layers

| Layer | Name | What it Tests | Speed | AI? |
|-------|------|--------------|-------|-----|
| **L0** | APM | Package structure, plugin.json validity | ~5s | No |
| **L1** | Lint | Frontmatter, cross-references, naming conventions | ~3s | No |
| **L2** | Unit | Trigger eval balance (positive/negative counts) | ~10s | No |
| **L3** | Trigger | Live trigger accuracy — does the right skill fire? | ~2m | Yes |
| **L4** | Session | Multi-turn workflows via tmux | ~5m | Yes |
| **L5** | Benchmark | Skill value — with vs without the skill | ~10m | Yes |

## Running Tests

```bash
# Fast tests (run after every change)
make test                          # L0 + L1 + L2 + pytest

# Live trigger tests
make test-triggers CLI=copilot     # L3 against Copilot
make test-triggers CLI=claude      # L3 against Claude

# Multi-turn session tests
make test-sessions CLI=copilot     # L4 against Copilot
make test-sessions CLI=claude      # L4 against Claude

# Skill value benchmark
make test-benchmark S=brain        # L5 for one skill

# Full matrix (both CLIs)
make test-all

# One skill, all layers
make test-skill S=brain

# Test inventory
make report
```

## L0: APM Verification

Validates that `plugin.json` has all required fields, all declared paths exist, agents have proper frontmatter, and skills have `SKILL.md` files.

```bash
make test-apm
```

## L1: Structure Validation

Runs `validate.py` which checks:
- `plugin.json` format and semver
- Agent frontmatter (name, description)
- Skill frontmatter and naming conventions
- Cross-references between AGENTS.md and agent files
- Orphan detection (CLAUDE.md, unused files)
- MCP server configuration

```bash
make lint
```

## L2: Trigger Eval Dry-Run

Validates that trigger eval JSON files are well-formed and balanced:
- Each file has a `skill_name` and `evals` array
- Each eval has `query` and `should_trigger` fields
- Minimum 8 positive and 5 negative evals per skill

```bash
make unit              # All skills
make unit S=brain      # One skill
```

## L3: Live Trigger Accuracy

Sends eval queries to a live AI assistant and checks whether the correct skill activates.

```bash
make test-triggers CLI=copilot     # Against Copilot CLI
make test-triggers CLI=claude      # Against Claude Code
make test-triggers CLI=copilot S=brain  # One skill
```

### Trigger Eval Format

```json
{
  "skill_name": "brain",
  "evals": [
    {
      "query": "what did we decide about using CNPG vs Azure Postgres?",
      "should_trigger": true
    },
    {
      "query": "run the smoke tests on cimpl/lab",
      "should_trigger": false,
      "note": "Test execution → osdu-qa"
    }
  ]
}
```

## L4: Session Tests

Spawns a tmux session, sends a sequence of prompts, and asserts on the output.

```bash
make test-sessions CLI=copilot S=brain
make test-sessions CLI=claude DEBUG=1  # Show tmux pane output
```

### Scenario Format

```json
{
  "name": "brain-workflow",
  "description": "Test brain skill — vault awareness and write discipline",
  "ready_pattern": "❯|\\$|>|claude",
  "steps": [
    {
      "name": "vault-awareness",
      "prompt": "what is the OSDU brain vault?",
      "timeout": 180,
      "assertions": [
        {
          "pattern": "00-inbox|01-goals|02-projects",
          "type": "regex",
          "description": "Knows vault directory structure"
        }
      ]
    }
  ]
}
```

## L5: Skill Value Benchmark

Compares AI performance with the skill enabled vs disabled on the same scenario.

```bash
make test-benchmark S=brain
```

Results are saved to `tests/benchmarks/`.

## Cross-Platform Matrix

The test framework supports both `copilot` and `claude` CLIs. The `CLI` variable controls which:

```bash
CLI=copilot make test-triggers  # Copilot
CLI=claude make test-triggers   # Claude
```

L3 and L4 tests should pass on both platforms. Trigger descriptions are written to be platform-agnostic.
